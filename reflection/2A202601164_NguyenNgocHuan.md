# Reflection Cá Nhân — Hackathon AI Batch 03

- **Họ và tên:** Nguyễn Ngọc Huân
- **Mã học viên:** 2A202601164
- **Nhóm:** Nemo vlearn
- **Phụ trách chính:** AI Backend (Groq API, Gemini fallback, prompt engineering, session management, xử lý lỗi/fallback & evaluation runner).
- **Tỷ lệ đóng góp:** 25%

---

## 1. Công việc thực tế đã triển khai

Trong suốt 1.5 ngày hackathon, tôi trực tiếp chịu trách nhiệm xây dựng toàn bộ hạ tầng **AI Backend** cho sản phẩm **Prototype AI Glossary Tutor cho VLearn**:

1. **Xây dựng FastAPI Backend Engine (`codebase/backend/app.py`):**
   - Đạt mốc Working Prototype với lời gọi AI thật 100%.
   - Thiết kế các RESTful endpoints: `/api/health`, `/api/sessions`, `/api/explain`, `/api/sessions/{session_id}/saved-terms`, `/api/chat`.

2. **Thiết kế Kiến trúc Đa Model & Fallback Chống Sụp (`llm_client.py`):**
   - Tích hợp **Groq AI** (`llama-3.3-70b-versatile`) làm mô hình chính phục vụ tốc độ phản hồi cực nhanh dưới 1.5 giây.
   - Xây dựng cơ chế Fallback 3 tầng: Groq Primary $\rightarrow$ Groq Secondary (`llama-3.1-8b-instant`) $\rightarrow$ Gemini API (`gemini-1.5-flash`) $\rightarrow$ Local Rule Engine.
   - Đảm bảo prototype hoạt động liên tục ngay cả khi gặp sự cố Quota (429), Server 503 hay mất kết nối mạng.

3. **Kỹ thuật Prompt Engineering & Safety Guard (`prompts.py`):**
   - Ép kiểu JSON Schema đầu ra nghiêm ngặt với các trường `term`, `expanded_form`, `meaning_in_context`, `plain_explanation`, `example`, `confidence`, `evidence_span`.
   - Thiết kế các quy tắc chống Prompt Injection trong tài liệu tiếng Anh, giải thích từ đa nghĩa theo ngữ cảnh (VD: `temperature`, `agent`) và tự động mở rộng acronyms.

4. **Xây dựng Bộ Benchmark Evaluator (`eval/golden_set.json`, `eval/run_eval.py`):**
   - Khai thác dữ liệu thực tế từ `data/vlearn-pack/chatlog/` và `data/vlearn-pack/transcript/` để tạo 24 test cases chuẩn bao phủ 4 lớp chỗ khó (§5).
   - Lập trình script `run_eval.py` đo đạc tự động Pass Rate, tỷ lệ vi phạm Safety, độ chính xác Acronym và Grounding evidence.

---

## 2. Bài học kinh nghiệm & Quyết định thiết kế đáng chú ý

- **Bài học về Prompt vs Schema:** Ban đầu LLM đôi khi trả về Markdown codeblock ` ```json `. Tôi đã viết thêm bộ lọc `clean_json_response` bằng Regex để đảm bảo JSON luôn được parse sạch sẽ 100%.
- **Bài học về Cost of Error:** Việc giải thích sai từ chuyên ngành AI gây hậu quả lớn hơn nhiều so với việc hỏi lại học viên. Do đó, tôi đã áp dụng tư duy **Conditional AI** — khi ngữ cảnh mơ hồ hoặc quá ngắn, AI chủ động đặt `confidence: "insufficient"` và yêu cầu học viên chọn thêm câu xung quanh thay vì đoán mò.
- **Bài học phối hợp nhóm:** Việc thống nhất API Schema (`schemas.py`) ngay từ đầu giúp Frontend (Vương Đức Thoại) và QA (Quách Thanh Hưng) phát triển độc lập mà không bị nghẽn tiến độ.

---

## 3. Tự đánh giá

Tôi đã hoàn thành 100% khối lượng công việc được giao đúng hạn, code có đầy đủ unit test tự động và báo cáo benchmark minh bạch. Tôi sẵn sàng giải thích chi tiết từng dòng code và quyết định kỹ thuật của mình trong buổi demo CP6.
