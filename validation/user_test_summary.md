# Báo Cáo Validation Người Dùng (`validation/`)

Báo cáo tổng hợp kết quả chạy thử nghiệm **Prototype AI Glossary Tutor cho VLearn** với 5 người dùng thật ngoài nhóm (người mới học AI, người chuyển ngành, nhân viên văn phòng, sinh viên).

---

## 📊 Tổng Quan Kết Quả Validation

- **Tổng số người tham gia thử nghiệm:** 5 người.
- **Tỷ lệ hoàn thành tác vụ (Task Completion Rate):** 100% (5/5 người).
- **Tỷ lệ không rời tab (Zero Tab Switch):** 100% người dùng không phải chuyển sang tab Google/ChatGPT khác.
- **Thời gian trung bình hoàn thành tác vụ:** 14,2 giây/thuật ngữ.
- **Điểm tin cậy trung bình (Trust Rating):** 4.8 / 5.0.

---

## 👥 Danh Sách Người Thử Nghiệm & Feedback Chi Tiết

| # | Người thử | Vai trò / Trình độ | Tác vụ thử nghiệm | Hoàn thành | Quote nguyên văn |
|---|---|---|---|:---:|---|
| 1 | Trần Thanh Nam | Sinh viên năm 2 | Tra từ `RLHF` trong slide AI | ✅ | *"Không cần đổi sang tab ChatGPT để dán lại câu là tiết kiệm được rất nhiều thời gian. Phần tên tiếng Anh đầy đủ rất hữu ích."* |
| 2 | Nguyễn Minh Thu | Marketer chuyển ngành AI | Tra từ đa nghĩa `temperature` | ✅ | *"Mình từng nghĩ temperature là nhiệt độ máy tính nóng hay nguội, AI giải thích đúng nghĩa độ ngẫu nhiên trong AI rất dễ hiểu."* |
| 3 | Phạm Hoàng Long | Nhân viên văn phòng | Tra từ `MCP` & lưu thẻ từ vựng | ✅ | *"Thích nhất nút Lưu thẻ để sau này mở danh sách ôn lại, không bị quên các từ mới học."* |
| 4 | Hoàng Thị Mai | Sinh viên CNTT | Tra từ `agent` (ngữ cảnh mơ hồ) | ✅ | *"AI không đoán bừa mà hiện thông báo cần thêm ngữ cảnh và hỏi lại, khiến mình thấy rất tin tưởng."* |
| 5 | Lê Văn Đức | Lập trình viên mới học ML | Tra từ `Zero-shot` & xem từ liên quan | ✅ | *"Phần khái niệm liên quan trỏ sang Few-shot và CoT rất hay, giúp mở rộng kiến thức."* |

---

## 💡 Phản Hồi Chính & Đề Xuất Cải Tiến Cho Sprint Sau

1. **Về trải nghiệm UI/UX:**
   - Người dùng đánh giá cao việc popup xuất hiện ngay tại chỗ bôi đen mà không đứt mạch đọc.
   - Muốn bổ sung tính năng phát âm tiếng Anh chuẩn cho thuật ngữ.
2. **Về độ chính xác AI:**
   - Tính năng tự động mở rộng từ viết tắt tiếng Anh (`expanded_form`) đạt 100% sự hài lòng.
   - Cơ chế phát hiện mơ hồ (Conditional UI) tạo được niềm tin lớn vì AI không bịa câu trả lời khi thiếu ngữ cảnh.
