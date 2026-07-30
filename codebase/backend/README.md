# VLearn Tutor API

Backend MVP không cần dependency ngoài Python 3. Chạy từ thư mục gốc:

```powershell
python codebase/backend/app.py
```

Tạo `.env` ở thư mục gốc:

```env
GROQ_API_KEY=your_key
GROQ_MODEL=llama-3.3-70b-versatile
GROQ_FALLBACK_MODEL=llama-3.3-70b-lite
```

Backend ưu tiên `GROQ_MODEL`. Khi model chính bị quota `429`, quá tải `503`
hoặc lỗi kết nối, request được thử lại bằng `GROQ_FALLBACK_MODEL`; response
luôn ghi model thực tế đã trả lời.

Base URL: `http://127.0.0.1:8000`.

## API

### `GET /api/health`

Kiểm tra server và số slide chunks đã nạp.

### `GET /api/slides`

Trả 58 trang slide đã xử lý cho frontend local. Dữ liệu nguồn và output
`data/vlearn-pack/processed/` không được commit; chạy
`python scripts/extract_slides.py` để tạo lại trên máy có data pack.

### `POST /api/sessions`

```json
{"initial_level": "coban"}
```

Tạo phiên học. Ba mức hợp lệ: `coban`, `thongthao`, `nangcao`.

### `GET /api/sessions/{session_id}`

Đọc trạng thái năng lực hiện tại.

### `PATCH /api/sessions/{session_id}`

```json
{"level": "thongthao"}
```

Cho học viên tự đổi mức. Logic cập nhật mức tự động sẽ được nối ở mốc 4.

### `POST /api/slides/search`

```json
{
  "query": "temperature ảnh hưởng việc chọn token thế nào?",
  "limit": 4,
  "document_id": "D1"
}
```

`document_id` là tùy chọn. API trả về nội dung, score và citation theo trang.

### `POST /api/chat`

```json
{
  "session_id": "id nhận từ POST /api/sessions",
  "message": "LLM chọn token tiếp theo như thế nào?"
}
```

Endpoint truy xuất context rồi gọi Groq để trả grounded answer dạng JSON. Server
chỉ chấp nhận citation nằm trong context đã truy xuất. Nếu không có nguồn đủ liên
quan, endpoint trả `status: insufficient_source` mà không gọi model.

## Trạng thái phiên

Phiên được lưu trong RAM để phù hợp prototype. Khởi động lại server sẽ xóa phiên;
không lưu dữ liệu người dùng lên đĩa.
