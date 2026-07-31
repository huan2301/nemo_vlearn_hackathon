# Reflection Cá Nhân — Hackathon AI Batch 03

- **Họ và tên:** Vương Đức Thoại
- **Mã học viên:** 2A202601770
- **Nhóm:** Nemo vlearn
- **Phụ trách chính:** Frontend — giao diện, slide PDF viewer, responsive, tích hợp API.
- **Tỷ lệ đóng góp:** 25%

---

## 1. Công việc thực tế đã triển khai

Tôi phụ trách toàn bộ frontend của **Prototype AI Glossary Tutor cho VLearn**, từ giao diện cơ bản đến việc dựng lại gần như toàn bộ trải nghiệm học sau khi backend được bổ sung API mới:

1. **Slide viewer thật, không phải ảnh chụp màn hình:** ban đầu chỉ demo bằng 1 đoạn text ngắn, sau đó thay bằng ảnh PNG chụp slide thật — nhưng nhận ra ảnh PNG không bôi đen được chữ, mất đúng trải nghiệm cốt lõi ("bôi đen từ để AI giải thích"). Đã chuyển hẳn sang render trực tiếp file PDF gốc bằng `pdf.js` (canvas + text layer riêng đè lên trên), tái hiện đúng cơ chế bôi đen như trình duyệt PDF gốc, rồi mở rộng thành viewer cuộn xem đủ nhiều trang liền mạch thay vì chỉ 1 trang.
2. **Dựng lại toàn bộ UI theo luồng học 11 bước** sau khi xác nhận backend đã có API hỗ trợ: chip gợi ý thuật ngữ khó theo từng trang, bộ chọn 4 cách học (Tóm tắt/Ví dụ/So sánh/Chuyên sâu), khối hiển thị độ khó + so sánh khái niệm quen thuộc, quiz trắc nghiệm kèm chấm điểm ngay tại chỗ, panel Learning Progress, và khu vực Flashcard "Cần ôn hôm nay" theo spaced repetition.
3. **Vá các lỗi CSS/JS tinh vi:** lỗi hiện đồng thời cả kết quả và thông báo lỗi (gốc rễ là CSS `[hidden]` bị `display:flex` của class khác đè mất, không phải race-condition như tưởng ban đầu); lỗi topbar xuống dòng; lỗi 8 trang slide bị bóp méo do thiếu `flex-shrink:0`; lỗi lệch vị trí lớp text chọn được trên slide do thiếu biến CSS `--scale-factor` mà `pdf.js` yêu cầu.
4. **Tăng độ bền cho trải nghiệm khi backend không ổn định:** thêm cơ chế tự phát hiện session cũ đã "chết" (do backend restart mất state trong RAM) và tự tạo lại + đồng bộ lại toàn bộ từ đã lưu, cộng thêm cache `localStorage` để Sổ tay ôn tập không bao giờ hiện trắng trơn dù mất mạng hay backend vừa khởi động lại.
5. **Chuẩn bị deploy miễn phí:** tách `API_BASE` ra file `config.js` riêng (tự nhận diện local vs. production), viết `render.yaml` và hướng dẫn deploy Render (backend) + Cloudflare Pages (frontend).

## 2. Bài học kinh nghiệm & quyết định thiết kế đáng chú ý

- **Triệu chứng không phải nguyên nhân:** lỗi "kết quả và lỗi hiện cùng lúc" ban đầu tôi nghĩ là race-condition ở JS (2 request chồng nhau), đã sửa theo hướng đó nhưng không hết. Gốc rễ thật sự lại nằm ở CSS — thuộc tính `[hidden]` bị 1 class `display:flex` khác đè mất hiệu lực. Bài học: khi 1 lỗi trông "hợp lý" theo 1 giả thuyết, vẫn cần tự hỏi "còn khả năng nào khác không" trước khi sửa, thay vì sửa theo phỏng đoán đầu tiên rồi coi là xong.
- **AI hỗ trợ thế nào:** tôi dùng Claude (qua Cowork) xuyên suốt để debug và build tính năng mới — đặc biệt hữu ích khi cần tra cứu chi tiết kỹ thuật ít gặp (VD: `pdf.js` yêu cầu biến CSS `--scale-factor` mới render đúng vị trí text) hoặc dựng nhanh 1 khối UI hoàn chỉnh (quiz + chấm điểm + progress) để kịp tiến độ. Nhưng cũng có lúc AI trả lời SAI vì đọc phải dữ liệu cache cũ — chỉ khi tôi yêu cầu "kiểm tra lại lần nữa" thì câu trả lời đúng mới được xác nhận. Bài học: AI là công cụ tăng tốc rất tốt, nhưng kết quả AI đưa ra (đặc biệt là "báo cáo trạng thái") vẫn cần được xác minh lại bằng bằng chứng cụ thể (source thật, log thật) chứ không nhận ngay là đúng.
- **Một bài học từ case fail của chính nhóm:** nhiều lần trong quá trình build, backend "trông như đã xong" (file mới được thêm, endpoint mới xuất hiện trong code) nhưng khi thực sự chạy thử mới lộ ra các file liên quan chưa được cập nhật đồng bộ — ví dụ 1 file phụ trợ bị đặt sai tên/sai thư mục nên import lỗi ngay khi khởi động server, hoặc lớp quản lý session thiếu hẳn vài hàm mà route mới đang gọi tới, hoặc prompt gửi cho AI chưa từng được cập nhật để yêu cầu đúng field mới (quiz, độ khó...) dù schema phía code đã khai báo sẵn. Tất cả đều "biên dịch được" nhưng không chạy đúng cho tới khi test end-to-end thật. Bài học cho cả nhóm: khi nhiều người cùng sửa các lớp khác nhau của cùng 1 tính năng (route, schema, prompt, state), chỉ kiểm tra từng file riêng lẻ là không đủ — phải chạy thử toàn bộ luồng thật (request thật, không phải chỉ đọc code) trước khi coi một tính năng là hoàn thành.

## 3. Tự đánh giá

Tôi đã hoàn thành phần frontend được giao, gồm cả phần phát sinh thêm (dựng lại UI theo luồng học đầy đủ khi backend được bổ sung API giữa chừng) và một số việc ngoài phạm vi ban đầu (debug các lỗi tích hợp phía backend khi phát hiện ra, chuẩn bị deploy). Tôi nắm rõ và giải thích được từng quyết định kỹ thuật của phần mình — đặc biệt là lý do chọn render PDF thật thay vì ảnh tĩnh, và cách hệ thống giữ được dữ liệu người học khi backend không ổn định — sẵn sàng trình bày chi tiết trong buổi demo CP6.
