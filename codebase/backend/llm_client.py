import json
import re
import urllib.request
import urllib.error
import logging
from typing import Dict, Any, Tuple, Optional
from config import config
from prompts import GLOSSARY_SYSTEM_PROMPT, CHAT_TUTOR_SYSTEM_PROMPT, QUIZ_ONLY_SYSTEM_PROMPT

logger = logging.getLogger("vlearn_llm_client")
logger.setLevel(logging.INFO)

# Optional import of google-generativeai
try:
    import google.generativeai as genai
    HAS_GEMINI_SDK = True
except ImportError:
    HAS_GEMINI_SDK = False


class LLMClient:
    def __init__(self):
        self.groq_api_key = config.GROQ_API_KEY
        self.groq_fallback_key = config.GROQ_FALLBACK_API_KEY
        self.groq_model = config.GROQ_MODEL
        self.groq_fallback_model = config.GROQ_FALLBACK_MODEL

        self.gemini_api_key = config.GEMINI_API_KEY
        self.gemini_model = config.GEMINI_PRIMARY_MODEL

    def _call_groq_api(self, api_key: str, model_name: str, messages: list, json_mode: bool = True) -> str:
        """Thực hiện HTTP call trực tiếp đến Groq API."""
        if not api_key:
            raise ValueError("Groq API key is empty")

        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "VLearn-AI-Tutor/1.0"
        }

        payload: Dict[str, Any] = {
            "model": model_name,
            "messages": messages,
            "temperature": 0.1
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        data_bytes = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data_bytes, headers=headers, method="POST")

        with urllib.request.urlopen(req, timeout=config.REQUEST_TIMEOUT) as response:
            resp_body = response.read().decode("utf-8")
            resp_json = json.loads(resp_body)
            return resp_json["choices"][0]["message"]["content"]

    def _call_gemini_api(self, api_key: str, model_name: str, prompt_text: str) -> str:
        """Thực hiện call đến Gemini API qua SDK hoặc REST fallback."""
        if not api_key:
            raise ValueError("Gemini API key is empty")

        # 1. Thử dùng Google Generative AI SDK nếu khả dụng
        if HAS_GEMINI_SDK:
            try:
                genai.configure(api_key=api_key)
                g_model = genai.GenerativeModel(model_name)
                response = g_model.generate_content(prompt_text)
                return response.text
            except Exception as e:
                logger.warning(f"Gemini SDK call failed ({e}), trying REST fallback...")

        # 2. REST API Fallback cho Gemini
        clean_model = "gemini-1.5-flash" if "gemini" not in model_name else model_name
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{clean_model}:generateContent?key={api_key}"
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [{
                "parts": [{"text": prompt_text}]
            }],
            "generationConfig": {
                "temperature": 0.1,
                "responseMimeType": "application/json"
            }
        }

        data_bytes = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data_bytes, headers=headers, method="POST")

        with urllib.request.urlopen(req, timeout=config.REQUEST_TIMEOUT) as response:
            resp_body = response.read().decode("utf-8")
            resp_json = json.loads(resp_body)
            return resp_json["candidates"][0]["content"]["parts"][0]["text"]

    def clean_json_response(self, text: str) -> Dict[str, Any]:
        """Làm sạch văn bản trả về để parse ra JSON object."""
        text = text.strip()
        if text.startswith("```"):
            text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
            text = re.sub(r"\s*```$", "", text)

        json_match = re.search(r"\{.*\}", text, re.DOTALL)
        if json_match:
            text = json_match.group(0)

        return json.loads(text)

    @staticmethod
    def _coerce_str(value: Any) -> Optional[str]:
        """LLM đôi khi trả sai kiểu cho 1 field lẽ ra phải là string — VD: `expanded_form`
        thành dict `{"AI": "Artificial Intelligence", "LLM": "Large Language Model"}` khi
        selected_text chứa nhiều từ viết tắt cùng lúc, thay vì đúng 1 string như schema yêu
        cầu. Không ép luôn về string thì pydantic ném ValidationError -> lỗi 500 cả request.
        Thay vì vậy, ép về 1 string dễ đọc; None vẫn giữ nguyên None (field optional)."""
        if value is None:
            return None
        if isinstance(value, str):
            return value
        if isinstance(value, dict):
            return "; ".join(f"{k}: {v}" for k, v in value.items())
        if isinstance(value, list):
            return "; ".join(str(v) for v in value)
        return str(value)

    def _normalize_explain_payload(self, parsed: Dict[str, Any]) -> Dict[str, Any]:
        """Đảm bảo các field mới (is_difficult, comparison_concept, quiz) luôn có mặt
        và hợp lệ dù model trả về thiếu field hoặc field sai định dạng (thiếu field,
        đúng field nhưng sai KIỂU dữ liệu, ...) — không để 1 field lệch format làm
        sập cả response."""
        # --- 1) Ép mọi field lẽ ra là string về đúng string, kể cả khi model trả nhầm
        #     kiểu (dict/list/number/bool...) — tránh ValidationError khi build ExplainResponse.
        for field in (
            "term", "confidence", "expanded_form", "meaning_in_context",
            "plain_explanation", "styled_explanation", "difficulty_reason",
            "example", "evidence_span", "clarifying_question",
        ):
            if field in parsed:
                parsed[field] = self._coerce_str(parsed[field])

        parsed.setdefault("is_difficult", False)
        parsed.setdefault("difficulty_reason", None)
        parsed.setdefault("comparison_concept", None)
        parsed.setdefault("related_concepts", [])
        if not parsed.get("styled_explanation"):
            parsed["styled_explanation"] = parsed.get("plain_explanation", "")

        # --- 2) Ép các field string lồng bên trong comparison_concept / related_concepts / quiz.
        cc = parsed.get("comparison_concept")
        if isinstance(cc, dict):
            cc["concept"] = self._coerce_str(cc.get("concept")) or ""
            cc["comparison"] = self._coerce_str(cc.get("comparison")) or ""

        related = parsed.get("related_concepts")
        if isinstance(related, list):
            for rc in related:
                if isinstance(rc, dict):
                    if "concept" in rc:
                        rc["concept"] = self._coerce_str(rc.get("concept")) or ""
                    if "relationship" in rc:
                        rc["relationship"] = self._coerce_str(rc.get("relationship")) or ""

        quiz = parsed.get("quiz")
        if isinstance(quiz, dict):
            quiz["question"] = self._coerce_str(quiz.get("question")) or ""
            quiz["correct_key"] = self._coerce_str(quiz.get("correct_key")) or ""
            quiz["explanation"] = self._coerce_str(quiz.get("explanation")) or ""
            if isinstance(quiz.get("options"), list):
                for opt in quiz["options"]:
                    if isinstance(opt, dict):
                        opt["key"] = self._coerce_str(opt.get("key")) or ""
                        opt["text"] = self._coerce_str(opt.get("text")) or ""

        confidence = parsed.get("confidence") or "high"
        quiz = parsed.get("quiz")

        # Không đủ ngữ cảnh -> không ép người học làm quiz / so sánh
        if confidence == "insufficient":
            parsed["quiz"] = None
            parsed["comparison_concept"] = None
            return parsed

        # Validate cấu trúc quiz tối thiểu, nếu sai định dạng thì bỏ qua thay vì lỗi 500
        if quiz:
            valid = (
                isinstance(quiz, dict)
                and quiz.get("question")
                and isinstance(quiz.get("options"), list)
                and len(quiz.get("options")) >= 2
                and quiz.get("correct_key")
                and any(opt.get("key") == quiz.get("correct_key") for opt in quiz.get("options", []) if isinstance(opt, dict))
            )
            if not valid:
                parsed["quiz"] = None

        return parsed

    def explain_term(self, selected_text: str, surrounding_context: str = "", learner_level: str = "coban", explain_style: str = "tomtat") -> Tuple[Dict[str, Any], str]:
        """
        Giải thích thuật ngữ AI theo luồng:
        Bôi đen -> Giải thích ngữ cảnh -> Đánh giá độ khó -> Người học chọn kiểu giải thích ->
        Sinh ví dụ -> So sánh khái niệm đã biết -> Quiz 1 câu.

        Fallback chain: Groq (Primary) -> Groq (Fallback) -> Gemini -> Rule-engine local.
        """
        if explain_style not in ("tomtat", "vidu", "sosanh", "chuyensau"):
            explain_style = "tomtat"

        user_prompt = f"""selected_text: "{selected_text}"
surrounding_context: "{surrounding_context}"
learner_level: "{learner_level}"
explain_style: "{explain_style}"
"""
        messages = [
            {"role": "system", "content": GLOSSARY_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ]

        errors = []

        # 1. Groq Primary Model
        if self.groq_api_key:
            try:
                raw_out = self._call_groq_api(self.groq_api_key, self.groq_model, messages, json_mode=True)
                parsed = self.clean_json_response(raw_out)
                parsed = self._normalize_explain_payload(parsed)
                return parsed, f"groq/{self.groq_model}"
            except Exception as e:
                err_msg = f"Groq Primary ({self.groq_model}) failed: {str(e)}"
                logger.warning(err_msg)
                errors.append(err_msg)

        # 2. Groq Fallback Model
        if self.groq_fallback_key or self.groq_api_key:
            key_to_use = self.groq_fallback_key or self.groq_api_key
            try:
                raw_out = self._call_groq_api(key_to_use, self.groq_fallback_model, messages, json_mode=True)
                parsed = self.clean_json_response(raw_out)
                parsed = self._normalize_explain_payload(parsed)
                return parsed, f"groq/{self.groq_fallback_model}"
            except Exception as e:
                err_msg = f"Groq Fallback ({self.groq_fallback_model}) failed: {str(e)}"
                logger.warning(err_msg)
                errors.append(err_msg)

        # 3. Gemini API
        if self.gemini_api_key:
            try:
                gemini_full_prompt = f"{GLOSSARY_SYSTEM_PROMPT}\n\nUSER INPUT:\n{user_prompt}"
                raw_out = self._call_gemini_api(self.gemini_api_key, self.gemini_model, gemini_full_prompt)
                parsed = self.clean_json_response(raw_out)
                parsed = self._normalize_explain_payload(parsed)
                return parsed, f"gemini/{self.gemini_model}"
            except Exception as e:
                err_msg = f"Gemini ({self.gemini_model}) failed: {str(e)}"
                logger.warning(err_msg)
                errors.append(err_msg)

        # 4. Rule-based fallback (bảo vệ prototype khi mất kết nối)
        logger.error(f"All LLM APIs failed. Errors: {errors}")
        fallback_data = self._generate_rule_fallback(selected_text, surrounding_context, learner_level, explain_style)
        return fallback_data, "fallback/local-rule-engine"

    def _coerce_quiz(self, quiz: Any) -> Optional[Dict[str, Any]]:
        """Ép kiểu + validate cấu trúc tối thiểu của 1 quiz object đứng riêng (không lồng
        trong response giải thích đầy đủ như _normalize_explain_payload). Trả None nếu
        không cứu được (thiếu field / sai cấu trúc) thay vì để lỗi lan ra ngoài."""
        if not isinstance(quiz, dict):
            return None
        quiz["question"] = self._coerce_str(quiz.get("question")) or ""
        quiz["correct_key"] = self._coerce_str(quiz.get("correct_key")) or ""
        quiz["explanation"] = self._coerce_str(quiz.get("explanation")) or ""
        options = quiz.get("options")
        if isinstance(options, list):
            for opt in options:
                if isinstance(opt, dict):
                    opt["key"] = self._coerce_str(opt.get("key")) or ""
                    opt["text"] = self._coerce_str(opt.get("text")) or ""
        valid = (
            bool(quiz.get("question"))
            and isinstance(options, list)
            and len(options) >= 2
            and bool(quiz.get("correct_key"))
            and any(isinstance(o, dict) and o.get("key") == quiz.get("correct_key") for o in options)
        )
        return quiz if valid else None

    def _generate_fallback_quiz(self, term: str, plain_explanation: str, example: str) -> Dict[str, Any]:
        """Quiz dự phòng khi cả Groq lẫn Gemini đều lỗi — dùng chính nội dung đã lưu
        (plain_explanation) làm đáp án đúng, để câu hỏi vẫn có ý nghĩa thay vì bịa vô căn cứ."""
        correct_text = (plain_explanation or f"Khái niệm liên quan đến {term}").strip()
        if len(correct_text) > 90:
            correct_text = correct_text[:87] + "..."
        return {
            "question": f"Theo giải thích đã lưu, '{term}' có nghĩa là gì?",
            "options": [
                {"key": "A", "text": correct_text},
                {"key": "B", "text": "Một loại ngôn ngữ lập trình"},
                {"key": "C", "text": "Một thiết bị phần cứng máy tính"},
                {"key": "D", "text": "Không liên quan gì đến lĩnh vực AI"},
            ],
            "correct_key": "A",
            "explanation": f"Đúng theo phần giải thích đã lưu: {plain_explanation}" if plain_explanation else "Đáp án A khớp với giải thích đã lưu cho thuật ngữ này.",
        }

    def generate_quiz_for_term(
        self, term: str, meaning_in_context: str = "", plain_explanation: str = "",
        example: str = "", learner_level: str = "coban"
    ) -> Tuple[Dict[str, Any], str]:
        """Sinh bổ sung ĐÚNG 1 câu quiz cho 1 thuật ngữ đã lưu sẵn (dùng cho 'Ôn tập tổng
        hợp' — những thẻ lưu từ trước khi có tính năng lưu-quiz-theo-thẻ). Cùng chuỗi
        fallback Groq -> Groq fallback -> Gemini -> rule-engine như explain_term, nhưng
        gọn hơn vì chỉ cần đúng 1 object quiz, không cần giải thích đầy đủ lại từ đầu."""
        user_prompt = f"""term: "{term}"
meaning_in_context: "{meaning_in_context}"
plain_explanation: "{plain_explanation}"
example: "{example}"
learner_level: "{learner_level}"
"""
        messages = [
            {"role": "system", "content": QUIZ_ONLY_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ]
        errors = []

        if self.groq_api_key:
            try:
                raw_out = self._call_groq_api(self.groq_api_key, self.groq_model, messages, json_mode=True)
                quiz = self._coerce_quiz(self.clean_json_response(raw_out))
                if quiz:
                    return quiz, f"groq/{self.groq_model}"
            except Exception as e:
                errors.append(f"Groq Primary failed: {e}")

        if self.groq_fallback_key or self.groq_api_key:
            key_to_use = self.groq_fallback_key or self.groq_api_key
            try:
                raw_out = self._call_groq_api(key_to_use, self.groq_fallback_model, messages, json_mode=True)
                quiz = self._coerce_quiz(self.clean_json_response(raw_out))
                if quiz:
                    return quiz, f"groq/{self.groq_fallback_model}"
            except Exception as e:
                errors.append(f"Groq Fallback failed: {e}")

        if self.gemini_api_key:
            try:
                full_prompt = f"{QUIZ_ONLY_SYSTEM_PROMPT}\n\nUSER INPUT:\n{user_prompt}"
                raw_out = self._call_gemini_api(self.gemini_api_key, self.gemini_model, full_prompt)
                quiz = self._coerce_quiz(self.clean_json_response(raw_out))
                if quiz:
                    return quiz, f"gemini/{self.gemini_model}"
            except Exception as e:
                errors.append(f"Gemini failed: {e}")

        logger.error(f"generate_quiz_for_term: all LLM APIs failed for '{term}'. Errors: {errors}")
        return self._generate_fallback_quiz(term, plain_explanation, example), "fallback/local-rule-engine"

    def chat_tutor(self, message: str, context: Optional[str] = None, history: Optional[list] = None) -> Tuple[str, str]:
        """Hỏi đáp với AI Tutor qua hội thoại."""
        full_context = f"Ngữ cảnh tài liệu: {context}\n\n" if context else ""
        user_msg = f"{full_context}Câu hỏi của học viên: {message}"

        messages = [{"role": "system", "content": CHAT_TUTOR_SYSTEM_PROMPT}]
        if history:
            messages.extend(history[-6:])
        messages.append({"role": "user", "content": user_msg})

        if self.groq_api_key:
            try:
                raw_out = self._call_groq_api(self.groq_api_key, self.groq_model, messages, json_mode=False)
                return raw_out, f"groq/{self.groq_model}"
            except Exception as e:
                logger.warning(f"Groq Chat failed: {e}")

        if self.gemini_api_key:
            try:
                prompt = f"{CHAT_TUTOR_SYSTEM_PROMPT}\n\n{user_msg}"
                raw_out = self._call_gemini_api(self.gemini_api_key, self.gemini_model, prompt)
                return raw_out, f"gemini/{self.gemini_model}"
            except Exception as e:
                logger.warning(f"Gemini Chat failed: {e}")

        return "Xin lỗi bạn, kết nối trợ lý AI hiện đang bận. Bạn vui lòng thử lại sau ít phút nhé!", "fallback/local"

    def _build_styled_explanation(self, term: str, plain_explanation: str, example: str, explain_style: str, comparison: Optional[Dict[str, str]] = None) -> str:
        """Sinh nội dung styled_explanation cho rule-engine fallback (khi không có LLM)."""
        if explain_style == "tomtat":
            first_sentence = plain_explanation.split(".")[0].strip()
            return f"{first_sentence}." if first_sentence else plain_explanation
        if explain_style == "vidu":
            return f"Ví dụ dễ hình dung: {example}"
        if explain_style == "sosanh":
            if comparison and comparison.get("concept") and comparison.get("comparison"):
                return f"So với '{comparison['concept']}': {comparison['comparison']}"
            return f"{plain_explanation} (Hãy liên hệ với 1 khái niệm quen thuộc bạn đã biết để dễ nhớ hơn.)"
        if explain_style == "chuyensau":
            return f"{plain_explanation} Về mặt kỹ thuật, đây là một khái niệm quan trọng trong pipeline huấn luyện/vận hành mô hình AI hiện đại, thường được nhắc tới cùng các kỹ thuật liên quan khác."
        return plain_explanation

    def _generate_rule_fallback(self, term: str, context: str, learner_level: str = "coban", explain_style: str = "tomtat") -> Dict[str, Any]:
        """Tự động tạo câu trả lời chuẩn mẫu (kèm difficulty + comparison + quiz + styled_explanation) khi offline/error."""
        term_clean = term.strip().upper()

        glossary_dict = {
            "RLHF": {
                "expanded_form": "Reinforcement Learning from Human Feedback",
                "meaning_in_context": "Phương pháp tinh chỉnh mô hình AI dựa trên đánh giá và phản hồi của con người.",
                "plain_explanation": "RLHF giúp AI trả lời lịch sự, an toàn và hữu ích hơn bằng cách để con người chấm điểm các câu trả lời của AI.",
                "example": "Con người chọn câu trả lời hay hơn giữa 2 phương án của AI, giúp AI rút kinh nghiệm.",
                "is_difficult": True,
                "difficulty_reason": "Đòi hỏi hiểu trước về học tăng cường (reinforcement learning) và quy trình huấn luyện mô hình.",
                "comparison_concept": {
                    "concept": "Dạy trẻ qua khen/chê",
                    "comparison": "Giống như cha mẹ khen khi trẻ làm đúng, chê khi làm sai để trẻ dần điều chỉnh hành vi."
                },
                "related_concepts": [
                    {"concept": "SFT", "relationship": "Giai đoạn học có giám sát trước khi làm RLHF"},
                    {"concept": "Reward Model", "relationship": "Mô hình thưởng mô phỏng sở thích con người"}
                ],
                "quiz": {
                    "question": "RLHF chủ yếu dùng để làm gì?",
                    "options": [
                        {"key": "A", "text": "Tăng tốc độ suy luận của mô hình"},
                        {"key": "B", "text": "Tinh chỉnh mô hình dựa trên phản hồi của con người"},
                        {"key": "C", "text": "Nén kích thước mô hình"},
                        {"key": "D", "text": "Dịch văn bản sang ngôn ngữ khác"}
                    ],
                    "correct_key": "B",
                    "explanation": "RLHF là kỹ thuật dùng đánh giá của con người để huấn luyện lại mô hình cho phù hợp hơn."
                }
            },
            "RNN": {
                "expanded_form": "Recurrent Neural Network",
                "meaning_in_context": "Mạng thần kinh hồi quy xử lý dữ liệu chuỗi theo thời gian.",
                "plain_explanation": "Mô hình AI xử lý từng từ trong câu và ghi nhớ thông tin của các từ trước đó.",
                "example": "Dự đoán từ tiếp theo trong câu bằng mô hình RNN.",
                "is_difficult": True,
                "difficulty_reason": "Cần hiểu khái niệm mạng nơ-ron và cơ chế xử lý tuần tự theo thời gian.",
                "comparison_concept": {
                    "concept": "Đọc truyện theo từng trang",
                    "comparison": "Giống như đọc truyện, bạn nhớ tình tiết trang trước để hiểu trang sau, RNN cũng nhớ từ trước để đoán từ sau."
                },
                "related_concepts": [
                    {"concept": "LSTM", "relationship": "Biến thể RNN giải quyết vấn đề nhớ xa"},
                    {"concept": "Sequential Data", "relationship": "Dữ liệu dạng chuỗi như văn bản, âm thanh"}
                ],
                "quiz": {
                    "question": "RNN phù hợp nhất để xử lý loại dữ liệu nào?",
                    "options": [
                        {"key": "A", "text": "Dữ liệu dạng chuỗi/tuần tự (văn bản, âm thanh)"},
                        {"key": "B", "text": "Ảnh tĩnh"},
                        {"key": "C", "text": "Bảng dữ liệu không có thứ tự"},
                        {"key": "D", "text": "Video 3D"}
                    ],
                    "correct_key": "A",
                    "explanation": "RNN được thiết kế để xử lý dữ liệu có tính tuần tự theo thời gian."
                }
            },
            "SFT": {
                "expanded_form": "Supervised Fine-Tuning",
                "meaning_in_context": "Bước tinh chỉnh mô hình AI có giám sát bằng các cặp dữ liệu câu hỏi-câu trả lời chuẩn.",
                "plain_explanation": "Học có giám sát giúp AI quen với định dạng trả lời trước khi tinh chỉnh bằng RLHF.",
                "example": "Dùng tập dữ liệu câu hỏi-đáp mẫu để huấn luyện AI phản hồi đúng cấu trúc.",
                "is_difficult": False,
                "difficulty_reason": None,
                "comparison_concept": {
                    "concept": "Học theo bài mẫu có đáp án",
                    "comparison": "Giống như học sinh luyện đề có đáp án mẫu để bắt chước cách trình bày đúng."
                },
                "related_concepts": [
                    {"concept": "RLHF", "relationship": "Bước tinh chỉnh tiếp theo sau SFT"},
                    {"concept": "Fine-Tuning", "relationship": "Quá trình huấn luyện lại mô hình"}
                ],
                "quiz": {
                    "question": "SFT sử dụng loại dữ liệu nào để huấn luyện?",
                    "options": [
                        {"key": "A", "text": "Dữ liệu không nhãn"},
                        {"key": "B", "text": "Cặp câu hỏi - câu trả lời mẫu (có giám sát)"},
                        {"key": "C", "text": "Chỉ hình ảnh"},
                        {"key": "D", "text": "Chỉ số liệu tài chính"}
                    ],
                    "correct_key": "B",
                    "explanation": "SFT là 'Supervised' Fine-Tuning nên cần dữ liệu có giám sát dạng cặp câu hỏi-đáp mẫu."
                }
            },
            "MCP": {
                "expanded_form": "Model Context Protocol",
                "meaning_in_context": "Giao thức chuẩn cho phép mô hình AI kết nối và tương tác an toàn với các nguồn dữ liệu ngoài.",
                "plain_explanation": "MCP đóng vai trò như cổng kết nối USB tiêu chuẩn giúp AI đọc file, truy vấn database hoặc gọi API tiện lợi.",
                "example": "AI kết nối với cơ sở dữ liệu local của công ty thông qua MCP server.",
                "is_difficult": True,
                "difficulty_reason": "Là khái niệm hệ thống/giao thức, cần hiểu về kiến trúc client-server và tool calling.",
                "comparison_concept": {
                    "concept": "Cổng USB-C",
                    "comparison": "Giống như cổng USB-C chuẩn hóa cách kết nối thiết bị, MCP chuẩn hóa cách AI kết nối với công cụ ngoài."
                },
                "related_concepts": [
                    {"concept": "Tool Calling", "relationship": "Khả năng AI gọi các công cụ ngoài"},
                    {"concept": "API", "relationship": "Giao diện lập trình ứng dụng kết nối hệ thống"}
                ],
                "quiz": {
                    "question": "MCP giúp AI làm được điều gì?",
                    "options": [
                        {"key": "A", "text": "Tăng số tham số của mô hình"},
                        {"key": "B", "text": "Kết nối chuẩn hóa với dữ liệu và công cụ bên ngoài"},
                        {"key": "C", "text": "Tự động dịch ngôn ngữ lập trình"},
                        {"key": "D", "text": "Giảm chi phí điện năng"}
                    ],
                    "correct_key": "B",
                    "explanation": "MCP là giao thức chuẩn hóa việc AI kết nối với nguồn dữ liệu/công cụ ngoài."
                }
            },
            "LLM": {
                "expanded_form": "Large Language Model",
                "meaning_in_context": "Mô hình ngôn ngữ lớn được huấn luyện trên lượng dữ liệu văn bản khổng lồ.",
                "plain_explanation": "Một hệ thống AI có khả năng hiểu, tóm tắt, dịch thuật và tạo văn bản tự nhiên như con người.",
                "example": "ChatGPT hay Claude là các mô hình LLM phổ biến.",
                "is_difficult": False,
                "difficulty_reason": None,
                "comparison_concept": {
                    "concept": "Một người đọc rất nhiều sách",
                    "comparison": "Giống như một người đã đọc hàng triệu cuốn sách nên có thể trò chuyện, viết lách về hầu hết mọi chủ đề."
                },
                "related_concepts": [
                    {"concept": "Transformer", "relationship": "Kiến trúc mạng cốt lõi của LLM"},
                    {"concept": "Token", "relationship": "Đơn vị văn bản nhỏ mà LLM xử lý"}
                ],
                "quiz": {
                    "question": "LLM là viết tắt của cụm từ nào?",
                    "options": [
                        {"key": "A", "text": "Large Language Model"},
                        {"key": "B", "text": "Long Learning Machine"},
                        {"key": "C", "text": "Linear Language Mapping"},
                        {"key": "D", "text": "Local Learning Module"}
                    ],
                    "correct_key": "A",
                    "explanation": "LLM = Large Language Model, mô hình ngôn ngữ lớn."
                }
            },
            "RAG": {
                "expanded_form": "Retrieval-Augmented Generation",
                "meaning_in_context": "Kỹ thuật kết hợp tìm kiếm dữ liệu ngoài với mô hình AI sinh văn bản.",
                "plain_explanation": "RAG giúp AI trả lời chính xác bằng cách tra cứu tài liệu thực tế trước khi sinh câu trả lời.",
                "example": "AI đọc tài liệu nội bộ công ty để trả lời câu hỏi chính xác.",
                "is_difficult": True,
                "difficulty_reason": "Kết hợp 2 kỹ thuật (tìm kiếm + sinh văn bản) nên cần hiểu cả hai phần trước.",
                "comparison_concept": {
                    "concept": "Thi mở tài liệu (open-book)",
                    "comparison": "Giống như thi mở sách: bạn tra cứu tài liệu trước rồi mới viết câu trả lời, thay vì học thuộc lòng."
                },
                "related_concepts": [
                    {"concept": "Vector Database", "relationship": "Nơi lưu trữ và tìm kiếm dữ liệu RAG"},
                    {"concept": "Embedding", "relationship": "Chuyển văn bản thành vectơ để tìm kiếm"}
                ],
                "quiz": {
                    "question": "Điểm khác biệt chính của RAG so với LLM thông thường là gì?",
                    "options": [
                        {"key": "A", "text": "RAG tra cứu tài liệu ngoài trước khi trả lời"},
                        {"key": "B", "text": "RAG chạy nhanh hơn gấp 10 lần"},
                        {"key": "C", "text": "RAG không cần dữ liệu huấn luyện"},
                        {"key": "D", "text": "RAG chỉ hoạt động với hình ảnh"}
                    ],
                    "correct_key": "A",
                    "explanation": "RAG = Retrieval-Augmented Generation, tức tra cứu (retrieval) rồi mới sinh (generation) câu trả lời."
                }
            }
        }

        matched = None
        for key, item in glossary_dict.items():
            if key in term_clean or term_clean in key:
                matched = item
                break

        if matched:
            plain_explanation = matched.get("plain_explanation", f"Giải thích ngắn gọn về {term}.")
            example_text = matched.get("example", f"Ví dụ minh họa cho {term}.")
            return {
                "term": term,
                "expanded_form": matched.get("expanded_form"),
                "meaning_in_context": matched.get("meaning_in_context", f"Nghĩa của {term} trong ngữ cảnh."),
                "plain_explanation": plain_explanation,
                "styled_explanation": self._build_styled_explanation(term, plain_explanation, example_text, explain_style, matched.get("comparison_concept")),
                "is_difficult": matched.get("is_difficult", False),
                "difficulty_reason": matched.get("difficulty_reason"),
                "example": example_text,
                "comparison_concept": matched.get("comparison_concept"),
                "related_concepts": matched.get("related_concepts", []),
                "confidence": "high",
                "evidence_span": context[:50] if context else term,
                "clarifying_question": None,
                "quiz": matched.get("quiz")
            }

        # Thuật ngữ tổng quát không có trong từ điển mẫu
        insufficient = not bool(context)
        generic_plain = f"'{term}' là một thuật ngữ kỹ thuật trong lĩnh vực AI và Khoa học máy tính."
        generic_example = f"Ứng dụng {term} giúp tối ưu hóa quá trình xử lý của mô hình AI."
        return {
            "term": term,
            "expanded_form": None,
            "meaning_in_context": f"Khái niệm '{term}' được đề cập trong đoạn văn bản đang đọc.",
            "plain_explanation": generic_plain,
            "styled_explanation": self._build_styled_explanation(term, generic_plain, generic_example, explain_style),
            "is_difficult": learner_level == "coban",
            "difficulty_reason": "Thiếu ngữ cảnh cụ thể nên có thể khó hình dung với người mới." if learner_level == "coban" else None,
            "example": generic_example,
            "comparison_concept": None,
            "related_concepts": [{"concept": "AI Concepts", "relationship": "Khái niệm liên quan"}],
            "confidence": "low" if context else "insufficient",
            "evidence_span": context[:40] if context else term,
            "clarifying_question": "Bạn có thể bôi đen thêm 1 câu xung quanh từ này để AI giải thích chính xác hơn không?" if not context else None,
            "quiz": None if insufficient else None
        }


llm_client = LLMClient()