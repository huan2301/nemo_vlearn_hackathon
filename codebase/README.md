# VLearn AI Tutor — Prototype (mức Working)

Prototype cho Hướng A – VLearn. Lát cắt: **học viên đang đọc slide bài giảng, gặp thuật ngữ AI không hiểu, bôi đen → AI giải thích đúng ngữ cảnh → kết quả là học viên hiểu ngay và có 1 flashcard để ôn lại sau.**

Luồng đầy đủ đã build: mở slide → hệ thống tự phát hiện thuật ngữ khó theo trình độ người học → bôi đen (hoặc bấm chip gợi ý) → AI giải thích theo ngữ cảnh → AI đánh giá độ khó → chọn 1 trong 4 cách học (Tóm tắt / Ví dụ / So sánh / Chuyên sâu) → so sánh với khái niệm quen thuộc → làm 1 câu quiz kiểm tra hiểu bài ngay → cập nhật Learning Profile → tự sinh flashcard → nhắc ôn lại theo spaced repetition (SM-2 rút gọn).

Mọi bước ra quyết định đều gọi AI thật (Groq, fallback Gemini, fallback cuối cùng là rule-engine local khi mất mạng/hết quota) — không có bước nào mock.

## Cấu trúc

```
codebase/
├── backend/                 FastAPI — xem codebase/backend/README.md để biết chi tiết API
└── frontend/
    ├── index.html
    ├── css/styles.css
    ├── js/
    │   ├── config.js          API_BASE — sửa 1 dòng này khi deploy (tự nhận diện local vs. production)
    │   └── app.js                toàn bộ logic: slide viewer (pdf.js), tra cứu, quiz, sổ tay, flashcard
    └── assets/
        └── slide-d1-selected.pdf   8 trang thật trích từ data/vlearn-pack/slides/d1-slide-hackathon.pdf
```

## Chạy local

```bash
# 1) Backend
cd codebase/backend
pip install -r requirements.txt
# tạo file .env với GROQ_API_KEY — xem codebase/backend/README.md
python app.py                # http://127.0.0.1:8000

# 2) Frontend — mở codebase/frontend/index.html bằng 1 static server (VD VS Code Live Server)
# KHÔNG mở trực tiếp bằng file:// — pdf.js cần chạy qua http(s) mới render được slide.
```

## Tính năng đã build

- **Slide viewer thật**: render trực tiếp file PDF gốc bằng pdf.js (canvas + text layer), cuộn xem đủ nhiều trang liền mạch, bôi đen chữ ngay trên slide y hệt trình duyệt PDF gốc — không phải ảnh chụp màn hình.
- Tự động quét mỗi trang, gợi ý thuật ngữ khó theo trình độ người học hiện tại (chip bấm nhanh, không cần tự bôi đen).
- Bôi đen bất kỳ cụm từ nào trên slide → AI giải thích đúng theo ngữ cảnh đoạn đang đọc (không giải thích chung chung).
- 4 cách học chọn được ngay tại chỗ sau khi có kết quả: Tóm tắt / Ví dụ / So sánh / Chuyên sâu.
- AI tự đánh giá thuật ngữ này có khó với trình độ hiện tại không + so sánh với 1 khái niệm quen thuộc để dễ hình dung.
- 1 câu quiz trắc nghiệm kiểm tra hiểu bài ngay sau khi đọc giải thích, chấm điểm tức thì, giải thích lại nếu sai.
- Learning Progress: điểm quiz, % trả lời đúng, streak đúng liên tiếp.
- Sổ tay ôn tập + Flashcard nhắc ôn theo spaced repetition (SM-2 rút gọn) — có cache `localStorage` nên không mất khi backend restart (chỉ mất lịch ôn tập chi tiết của từng thẻ, không mất danh sách từ).

## Deploy miễn phí

Xem `DEPLOY.md` ở gốc repo: Render (backend) + Cloudflare Pages (frontend), cả hai đều $0, không cần thẻ.

## Lưu ý dữ liệu & bảo mật

- `.env` chứa API key thật — không commit (đã có trong `.gitignore`, pattern `*.env`).
- Slide dùng để demo trên frontend chỉ là bản trích 8 trang (`assets/slide-d1-selected.pdf`), không phải file gốc đầy đủ.
- **Cần nhóm tự kiểm tra lại**: thư mục `data/vlearn-pack/` (chatlog CSV, 6 transcript, 2 file PDF slide gốc) hiện đang được `git` theo dõi trong repo này — nên rà lại với quy định "không commit data pack vào repo nộp bài" ở `01-de-bai.md` trước khi nộp bài.
