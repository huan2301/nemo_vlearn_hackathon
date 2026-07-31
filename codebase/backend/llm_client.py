import json
import re
import urllib.request
import urllib.error
import logging
from typing import Dict, Any, Tuple, Optional
from config import config
from prompts import GLOSSARY_SYSTEM_PROMPT, CHAT_TUTOR_SYSTEM_PROMPT

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
        # Model default safety fallback if model_name has custom local tag
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
        # Loại bỏ markdown wrapper ```json ... ```
        if text.startswith("```"):
            text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
            text = re.sub(r"\s*```$", "", text)

        # Regex tìm JSON object {}
        json_match = re.search(r"\{.*\}", text, re.DOTALL)
        if json_match:
            text = json_match.group(0)

        return json.loads(text)

    def explain_term(self, selected_text: str, surrounding_context: str = "", learner_level: str = "coban") -> Tuple[Dict[str, Any], str]:
        """
        Giải thích thuật ngữ AI dựa trên selected_text và surrounding_context.
        Sử dụng chuỗi Fallback:
        1. Groq (Primary Model)
        2. Groq (Fallback Model)
        3. Gemini API
        4. Mock fallback phòng khi tất cả API failure (dành cho demo/testing).
        """
        user_prompt = f"""selected_text: "{selected_text}"
surrounding_context: "{surrounding_context}"
learner_level: "{learner_level}"
"""
        messages = [
            {"role": "system", "content": GLOSSARY_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ]

        errors = []

        # 1. Thử gọi Groq Primary Model
        if self.groq_api_key:
            try:
                raw_out = self._call_groq_api(self.groq_api_key, self.groq_model, messages, json_mode=True)
                parsed = self.clean_json_response(raw_out)
                return parsed, f"groq/{self.groq_model}"
            except Exception as e:
                err_msg = f"Groq Primary ({self.groq_model}) failed: {str(e)}"
                logger.warning(err_msg)
                errors.append(err_msg)

        # 2. Thử gọi Groq Fallback Model
        if self.groq_fallback_key or self.groq_api_key:
            key_to_use = self.groq_fallback_key or self.groq_api_key
            try:
                raw_out = self._call_groq_api(key_to_use, self.groq_fallback_model, messages, json_mode=True)
                parsed = self.clean_json_response(raw_out)
                return parsed, f"groq/{self.groq_fallback_model}"
            except Exception as e:
                err_msg = f"Groq Fallback ({self.groq_fallback_model}) failed: {str(e)}"
                logger.warning(err_msg)
                errors.append(err_msg)

        # 3. Thử gọi Gemini API
        if self.gemini_api_key:
            try:
                gemini_full_prompt = f"{GLOSSARY_SYSTEM_PROMPT}\n\nUSER INPUT:\n{user_prompt}"
                raw_out = self._call_gemini_api(self.gemini_api_key, self.gemini_model, gemini_full_prompt)
                parsed = self.clean_json_response(raw_out)
                return parsed, f"gemini/{self.gemini_model}"
            except Exception as e:
                err_msg = f"Gemini ({self.gemini_model}) failed: {str(e)}"
                logger.warning(err_msg)
                errors.append(err_msg)

        # 4. Fallback thông minh phòng khi mất kết nối / API error (Bảo vệ Prototype)
        logger.error(f"All LLM APIs failed. Errors: {errors}")
        fallback_data = self._generate_rule_fallback(selected_text, surrounding_context)
        return fallback_data, "fallback/local-rule-engine"

    def chat_tutor(self, message: str, context: Optional[str] = None, history: Optional[list] = None) -> Tuple[str, str]:
        """Hỏi đáp với AI Tutor qua hội thoại."""
        full_context = f"Ngữ cảnh tài liệu: {context}\n\n" if context else ""
        user_msg = f"{full_context}Câu hỏi của học viên: {message}"

        messages = [{"role": "system", "content": CHAT_TUTOR_SYSTEM_PROMPT}]
        if history:
            messages.extend(history[-6:]) # Lấy 6 lượt gần nhất
        messages.append({"role": "user", "content": user_msg})

        # 1. Groq Primary
        if self.groq_api_key:
            try:
                raw_out = self._call_groq_api(self.groq_api_key, self.groq_model, messages, json_mode=False)
                return raw_out, f"groq/{self.groq_model}"
            except Exception as e:
                logger.warning(f"Groq Chat failed: {e}")

        # 2. Gemini Fallback
        if self.gemini_api_key:
            try:
                prompt = f"{CHAT_TUTOR_SYSTEM_PROMPT}\n\n{user_msg}"
                raw_out = self._call_gemini_api(self.gemini_api_key, self.gemini_model, prompt)
                return raw_out, f"gemini/{self.gemini_model}"
            except Exception as e:
                logger.warning(f"Gemini Chat failed: {e}")

        return "Xin lỗi bạn, kết nối trợ lý AI hiện đang bận. Bạn vui lòng thử lại sau ít phút nhé!", "fallback/local"

    def _generate_rule_fallback(self, term: str, context: str) -> Dict[str, Any]:
        """Tự động tạo câu trả lời chuẩn mẫu cho các thuật ngữ AI phổ biến khi offline/error."""
        term_clean = term.strip().upper()
        
        # Từ điển thuật ngữ mẫu phổ biến
        glossary_dict = {
            "RLHF": {
                "expanded_form": "Reinforcement Learning from Human Feedback",
                "meaning_in_context": "Phương pháp tinh chỉnh mô hình AI dựa trên đánh giá và phản hồi của con người.",
                "plain_explanation": "RLHF giúp AI trả lời lịch sự, an toàn và hữu ích hơn bằng cách để con người chấm điểm các câu trả lời của AI.",
                "example": "Con người chọn câu trả lời hay hơn giữa 2 phương án của AI, giúp AI rút kinh nghiệm.",
                "related_concepts": [
                    {"concept": "SFT", "relationship": "Giai đoạn học có giám sát trước khi làm RLHF"},
                    {"concept": "Reward Model", "relationship": "Mô hình thưởng mô phỏng sở thích con người"}
                ]
            },
            "MCP": {
                "expanded_form": "Model Context Protocol",
                "meaning_in_context": "Giao thức chuẩn cho phép mô hình AI kết nối và tương tác an toàn với các nguồn dữ liệu ngoài.",
                "plain_explanation": "MCP đóng vai trò như cổng kết nối USB tiêu chuẩn giúp AI đọc file, truy vấn database hoặc gọi API tiện lợi.",
                "example": "AI kết nối với cơ sở dữ liệu local của công ty thông qua MCP server.",
                "related_concepts": [
                    {"concept": "Tool Calling", "relationship": "Khả năng AI gọi các công cụ ngoài"},
                    {"concept": "API", "relationship": "Giao diện lập trình ứng dụng kết nối hệ thống"}
                ]
            },
            "LLM": {
                "expanded_form": "Large Language Model",
                "meaning_in_context": "Mô hình ngôn ngữ lớn được huấn luyện trên lượng dữ liệu văn bản khổng lồ.",
                "plain_explanation": "Một hệ thống AI có khả năng hiểu, tóm tắt, dịch thuật và tạo văn bản tự nhiên như con người.",
                "example": "ChatGPT hay Claude là các mô hình LLM phổ biến.",
                "related_concepts": [
                    {"concept": "Transformer", "relationship": "Kiến trúc mạng xã hội cốt lõi của LLM"},
                    {"concept": "Token", "relationship": "Đơn vị văn bản nhỏ mà LLM xử lý"}
                ]
            }
        }

        if term_clean in glossary_dict:
            item = glossary_dict[term_clean]
            return {
                "term": term,
                "expanded_form": item["expanded_form"],
                "meaning_in_context": item["meaning_in_context"],
                "plain_explanation": item["plain_explanation"],
                "example": item["example"],
                "related_concepts": item["related_concepts"],
                "confidence": "high",
                "evidence_span": context[:50] if context else term,
                "clarifying_question": None
            }

        # Thuật ngữ tổng quát không có trong từ điển mẫu
        return {
            "term": term,
            "expanded_form": None,
            "meaning_in_context": f"Khái niệm '{term}' được đề cập trong đoạn văn bản đang đọc.",
            "plain_explanation": f"'{term}' là một thuật ngữ kỹ thuật trong lĩnh vực AI và Khoa học máy tính.",
            "example": f"Ứng dụng {term} giúp tối ưu hóa quá trình xử lý của mô hình AI.",
            "related_concepts": [{"concept": "AI Concepts", "relationship": "Khái niệm liên quan"}],
            "confidence": "low" if context else "insufficient",
            "evidence_span": context[:40] if context else term,
            "clarifying_question": "Bạn có thể bôi đen thêm 1 câu xung quanh từ này để AI giải thích chính xác hơn không?" if not context else None
        }

llm_client = LLMClient()
