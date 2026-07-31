# VLearn AI Tutor — Backend API

FastAPI backend cho AI Glossary Tutor: bôi đen thuật ngữ → AI giải thích theo ngữ cảnh → đánh giá độ khó → chọn 1 trong 4 cách học → so sánh với khái niệm quen thuộc → quiz 1 câu kiểm tra hiểu bài → cập nhật Learning Profile → tự sinh flashcard → nhắc ôn theo spaced repetition (SM-2 rút gọn).

## Cài đặt & chạy

```bash
cd codebase/backend
pip install -r requirements.txt
python app.py
```

Mặc định chạy tại `http://127.0.0.1:8000` (Swagger docs tự sinh tại `/docs`).

### Biến môi trường

Tạo file `.env` NGAY TRONG `codebase/backend/` (không phải thư mục gốc repo — xem `config.py`):

```env
GROQ_API_KEY=your_key
GROQ_FALLBACK_API_KEY=            # để trống thì tự dùng lại GROQ_API_KEY
GROQ_MODEL=llama-3.3-70b-versatile
GROQ_FALLBACK_MODEL=llama-3.3-70b-lite
GEMINI_API_KEY=your_key            # tuỳ chọn — fallback tầng 3
GEMINI_PRIMARY_MODEL=gemini-1.5-flash
GEMINI_FALLBACK_MODEL=gemini-1.5-flash-8b
```

`.env` nằm trong `.gitignore` (pattern `*.env`) — không bao giờ commit key thật lên GitHub.

### Build slide index (tuỳ chọn — bật tính năng retrieval)

```bash
python build_index.py --input ../../data --output ../../data/slide_index.jsonl
```

Đọc cả `.pdf` (2 bộ slide thật trong `data/vlearn-pack/slides/`, tách text đúng theo từng trang PDF bằng `pypdf`) và `.txt`/`.md` (transcript). Kết quả phục vụ `/api/slides/search` và tự bù ngữ cảnh khi `surrounding_context` gửi lên quá ngắn (`_maybe_retrieve_context` trong `app.py`). Không bắt buộc — thiếu file `slide_index.jsonl` thì retrieval chỉ tắt lặng lẽ, mọi API khác vẫn chạy bình thường.

## API chính

| Method | Path | Việc gì |
|---|---|---|
| GET | `/api/health` | Kiểm tra backend + trạng thái Groq/Gemini |
| POST | `/api/sessions` | Tạo phiên học mới (`initial_level`: coban / thongthao / nangcao) |
| GET, PATCH | `/api/sessions/{id}` | Đọc / đổi mức người học |
| POST | `/api/terms/detect` | Quét 1 trang slide, trả về thuật ngữ khó (bước "mở slide") |
| POST | `/api/slides/search` | Tra cứu ngữ cảnh slide/transcript thật (cần đã build index) |
| POST | `/api/explain` (alias `/api/glossary/explain`) | Bôi đen → giải thích theo ngữ cảnh, kèm độ khó / so sánh / quiz |
| POST | `/api/quiz/submit` | Chấm quiz, cập nhật Learning Progress + lịch ôn flashcard |
| GET | `/api/sessions/{id}/progress` | Learning Progress (điểm quiz, % đúng, streak) |
| GET | `/api/sessions/{id}/flashcards/due` | Flashcard tới hạn ôn (spaced repetition) |
| POST | `/api/sessions/{id}/flashcards/{term_id}/review` | Học viên tự chấm mức nhớ, cập nhật lịch SM-2 |
| POST, GET, DELETE | `/api/sessions/{id}/saved-terms` | Sổ tay ôn tập (lưu / xem / xoá thuật ngữ) |
| POST | `/api/chat` | Hỏi đáp tự do với AI Tutor |

Chi tiết request/response đầy đủ: mở `/docs` khi server đang chạy.

## Kiến trúc

```
app.py                    FastAPI routes
schemas.py                 Pydantic request/response models
llm_client.py                Gọi Groq -> Groq fallback -> Gemini -> rule-engine local;
                               ép kiểu an toàn output LLM trước khi build response
prompts.py                     System prompt cho glossary explain + chat tutor
sessions.py                      SessionManager — state trong RAM (session, saved terms,
                                  learning progress, lịch ôn SM-2)
retriever.py / retriever_provider.py   BM25-like search trên slide_index.jsonl
build_index.py                          Dựng slide_index.jsonl từ PDF slide thật + transcript
config.py                                 Đọc .env
eval_logger.py                              Ghi log mỗi lượt explain thật vào eval/live_interactions.jsonl
```

## Trạng thái phiên (quan trọng khi deploy free tier)

Session / saved-terms / learning-progress lưu **trong RAM**, không có DB. Restart server (hoặc host free-tier tự ngủ rồi thức dậy) sẽ xoá hết — đây là lý do frontend có thêm lớp cache `localStorage` và tự "resync" lại danh sách từ đã lưu khi phát hiện session cũ đã mất (xem `codebase/frontend/js/app.js`, hàm `resyncSavedTermsToSession`).

## Deploy

Xem `DEPLOY.md` ở gốc repo — Render (backend, free) + Cloudflare Pages (frontend, free). File `render.yaml` ở gốc repo đã cấu hình sẵn build/start command cho Render.
