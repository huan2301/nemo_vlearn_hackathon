# VLearn AI Tutor — MVP Prototype

## Mô tả

Prototype AI Tutor cho VLearn giúp người học hiểu nhanh các thuật ngữ AI ngay khi đọc tài liệu tiếng Anh. Chỉ cần bôi đen từ chưa hiểu, AI sẽ giải thích ngay theo ngữ cảnh và cho phép lưu lại để ôn tập sau.

```
Đọc tài liệu → Bôi đen từ/cụm từ chưa hiểu → Icon AI xuất hiện → Bấm icon →
AI phân tích ngữ cảnh và giải thích →
Hiển thị:
Tên đầy đủ (nếu là từ viết tắt)
Nghĩa tiếng Việt
Giải thích dễ hiểu
Ví dụ minh họa
Lĩnh vực liên quan
→ Lưu vào sổ tay để ôn tập sau
```

## Cấu trúc

```
codebase/
├── backend/
│   ├── main.py            # FastAPI server
│   ├── ai_agent.py        # AI Agent (Groq)
│   ├── data_loader.py     # Parse transcript bài giảng
│   ├── requirements.txt   # Dependencies
│   ├── .env               # API key (KHÔNG commit)
│   └── .env.example       # Template
└── frontend/
    ├── index.html          # Trang chính
    ├── css/styles.css      # Styling
    └── js/app.js           # Logic tương tác
```

## Cách chạy

### 1. Cài đặt dependencies

```bash
cd codebase/backend
pip install -r requirements.txt
```

### 2. Cấu hình API key

```bash
# Tạo file .env trong codebase/backend/
cp .env.example .env
# Sửa GROQ_API_KEY trong file .env
```

### 3. Chạy server

```bash
cd codebase/backend
python -m uvicorn main:app --reload --port 8000
```

### 4. Mở trình duyệt

Truy cập: http://localhost:8000

## Tech Stack

- **Backend:** Python FastAPI
- **AI:** Groq LLM (configured via GROQ_API_KEY)
- **Frontend:** HTML / CSS / JavaScript (thuần)
- **Data:** 6 transcript bài giảng bản sạch (~700 đoạn có mã trích dẫn)

## Lưu ý

- File `.env` chứa API key — KHÔNG commit lên repo
- Data trong `data/vlearn-pack/` chỉ dùng trong phạm vi hackathon
- Prototype mức **Working** — chạy end-to-end với data thật
- AI call thật ở quyết định trung tâm (sinh câu hỏi, trả lời, sinh quiz)
