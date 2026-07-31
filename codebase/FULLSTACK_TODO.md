# Fullstack Developer — Việc cần làm (Vương Đức Thoại)

> File này để trả lời: **"làm gì trước khi AI Engineer (Nguyễn Ngọc Huân) xong phần LLM?"**
> Nguyên tắc: FE và AI logic tách rời qua **1 hợp đồng API cố định** → hai người code song song, không ai chờ ai.

---

## 1. Đã có sẵn — dùng làm nền

`prototype/ai-glossary-tutor.html` + `prototype/flow.html` (đã làm qua Cowork) đã có đủ:
bôi đen từ tự do → icon ⚡ hiện cạnh từ (kiểu DDICT) → popup kết quả → sổ tay ôn tập.

→ Việc của bạn KHÔNG phải làm lại từ đầu, mà là **chuyển bản demo này thành code thật trong `codebase/`** (tách file, tổ chức thư mục), rồi thay phần "từ điển giả cứng trong JS" bằng **1 lời gọi API thật**.

---

## 2. Làm NGAY — không cần chờ AI Engineer

- [ ] Dựng cấu trúc `codebase/` (frontend/, hoặc `manifest.json` + content script + popup nếu làm Chrome Extension thật thay vì Web App)
- [ ] Chuyển `ai-glossary-tutor.html` thành code có tổ chức (tách HTML/CSS/JS nếu cần) — giữ nguyên toàn bộ UI đã có
- [ ] Hoàn thiện chức năng bôi đen: bắt sự kiện `mouseup`, tính vị trí đặt icon — đã có, chỉnh cho chạy ổn định trên nhiều loại trang/đoạn văn bản khác nhau
- [ ] Popup kết quả: thêm đủ các **trạng thái UI** (hiện tại mới có "thành công"):
  - [ ] `loading` — đang gọi AI (spinner ngay trong popup)
  - [ ] `error` — API lỗi/timeout → thông báo + nút thử lại
  - [ ] `low-confidence` — AI không chắc nghĩa → hiển thị "chưa chắc chắn, hỏi tutor VLearn" (đúng đường ① trong `flow.html`)
- [ ] Sổ tay ôn tập (lưu local) — làm được 100% ngay, không phụ thuộc AI
- [ ] Viết **1 mock API function** trả JSON giả đúng hợp đồng ở mục 3 bên dưới — để bạn test toàn bộ luồng FE mà không cần chờ ai
- [ ] Commit sớm lên `codebase/` — CP2 (12:00 N1 / 17:00 N1) chỉ cần **"flow chính bấm hết được"**, prototype hiện tại đã đạt được điều này, chỉ cần đẩy lên repo đúng hạn

---

## 3. Hợp đồng API — thống nhất với AI Engineer NGAY HÔM NAY

Gửi bảng này cho Huân (AI Engineer) trước khi cả hai bắt tay code, để không ai đợi ai:

**Request (FE gửi đi):**
```json
{
  "term": "RAG",
  "context": "Retrieval-Augmented Generation (RAG) solves this problem by letting the system retrieve relevant information first...",
  "user_level": "beginner"
}
```

**Response (AI Engineer trả về):**
```json
{
  "status": "ok",              // "ok" | "low_confidence" | "error"
  "term": "RAG",
  "full_name": "Retrieval-Augmented Generation",
  "vi_meaning": "Sinh nội dung tăng cường bằng truy xuất",
  "explanation": "...",
  "example": "...",
  "field": "Generative AI / NLP",
  "related": ["Embedding", "Vector Database", "LLM"]
}
```
Khi `status = "low_confidence"` hoặc `"error"`: chỉ cần trả `status` + `term`, các trường còn lại có thể rỗng — FE tự hiển thị đúng UI trạng thái tương ứng (mục 2).

→ Việc này quan trọng nhất trong danh sách: chốt xong hợp đồng này, bạn code FE với mock function giả lập đúng hình dạng trên, Huân code AI logic trả đúng hình dạng trên — ráp lại là chạy, không phải sửa lại cấu trúc.

---

## 4. Chỉ làm SAU KHI AI Engineer có endpoint thật

- [ ] Thay mock function bằng `fetch()` gọi API thật của Huân
- [ ] Test lại đủ 3 trạng thái (ok / low_confidence / error) với dữ liệu thật
- [ ] Xoá `console.log`/hardcode còn sót, đảm bảo **không còn từ điển giả** nào chạy ngầm (CP3 yêu cầu rõ: *"lời gọi AI thật, không hardcode"*)
- [ ] Phối hợp Huân + Hưng (QA) chạy thử golden set ≥20 case ngay trên UI thật

---

## 5. Mốc cần nhớ (theo `04-rubric.md`)

| Mốc | Yêu cầu liên quan tới Fullstack |
|---|---|
| **CP2** | Flow chính bấm hết được (Sketch/Mock đủ) — **prototype hiện tại đã đạt**, chỉ cần commit đúng hạn |
| **CP3** | Lời gọi AI **thật**, không hardcode — cần API thật từ AI Engineer ráp vào |
| **CP5** | Bạn phải tự giải thích được phần code có tên mình (vibe-coding rule) — dù dùng AI hỗ trợ build |
