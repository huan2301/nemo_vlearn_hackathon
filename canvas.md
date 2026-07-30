# CP1 CANVAS — AI Glossary Tutor

**Tên đề tài:** AI Glossary Tutor — Trợ lý giải thích thuật ngữ AI theo ngữ cảnh cho người mới học

| # | Thành phần | Nội dung |
|---:|---|---|
| 1 | **Hướng** | **Hướng C — Làn mở · Tính năng AI mới.** Xây dựng AI Tutor hỗ trợ giải thích thuật ngữ AI theo đúng ngữ cảnh tài liệu đang đọc, giúp người học hiểu nhanh mà không phải chuyển sang công cụ khác. |
| 2 | **Job executor** | Người mới học AI (non-tech), sinh viên hoặc người chuyển ngành đang đọc tài liệu, slide hoặc bài viết về AI và gặp thuật ngữ chuyên ngành khó hiểu. |
| 3 | **Pain** | Trong quá trình học AI, người dùng thường xuyên gặp các thuật ngữ và từ viết tắt như LLM, RAG, Embedding, Fine-tuning... nhưng không hiểu ý nghĩa theo ngữ cảnh. Họ phải liên tục mở Google, ChatGPT hoặc các website khác để tra cứu, làm gián đoạn quá trình học và đôi khi vẫn hiểu sai khái niệm. |
| 4 | **Evidence ban đầu** | Quan sát ban đầu từ người học AI và sinh viên cho thấy việc tra cứu thuật ngữ diễn ra rất thường xuyên trong mỗi buổi học. Nhiều công cụ hiện nay chỉ dịch nghĩa hoặc trả lời chung chung mà chưa giải thích theo đúng ngữ cảnh của đoạn văn đang đọc. Nhóm sẽ xác thực bằng khảo sát ≥20 người và thu thập các ví dụ thực tế trong quá trình học để bổ sung evidence ở các checkpoint tiếp theo. |
| 5 | **Lát cắt MỘT CÂU** | **Khi một người mới học AI đang đọc tài liệu và bôi đen một thuật ngữ AI, hệ thống phân tích ngữ cảnh của đoạn văn để quyết định ý nghĩa phù hợp của thuật ngữ, rồi trả về phần giải thích dễ hiểu, mở rộng từ viết tắt và ví dụ minh họa giúp người học tiếp tục đọc mà không bị gián đoạn.** |
| 6 | **Automation + willing users** | **Conditional Automation:** AI chỉ đưa ra giải thích khi xác định được ngữ cảnh đủ rõ; nếu độ tin cậy thấp sẽ thông báo "chưa đủ ngữ cảnh để giải thích chính xác" và yêu cầu người dùng chọn thêm nội dung. Người dùng luôn có quyền xem lại, đặt câu hỏi tiếp hoặc yêu cầu giải thích theo mức độ cơ bản/nâng cao. **Willing users:** (1) `[Bổ sung tên]`; (2) `[Bổ sung tên]`; (3) `[Bổ sung tên]`. |
| 7 | **Phân công có tên** | **[Tên thành viên 1] — Product Lead & Spec Owner:** Canvas, JTBD, khảo sát, spec và demo.<br>**[Tên thành viên 2] — AI Engineer:** Prompt Engineering, tích hợp LLM, xử lý ngữ cảnh và AI Decision.<br>**[Tên thành viên 3] — Fullstack Developer:** Frontend, Backend, giao diện bôi đen, popup và tích hợp hệ thống.<br>**[Tên thành viên 4] — QA & Evaluation:** Golden Set, Quality Bar, Evaluation, Validation, Feedback Log và Reflection. |

## Giới hạn phạm vi tại CP1

- Không dịch toàn bộ tài liệu hoặc toàn bộ trang web.
- Không thay thế chatbot hỏi đáp tổng quát.
- Không tạo khóa học AI hoặc lộ trình học tập.
- Không giải thích các thuật ngữ ngoài lĩnh vực AI nếu không có ngữ cảnh phù hợp.
- Chỉ tập trung vào việc hỗ trợ giải thích thuật ngữ AI theo ngữ cảnh của nội dung người dùng đang đọc.
- Evidence, khảo sát người dùng và Quality Bar sẽ được bổ sung và cập nhật trong các checkpoint tiếp theo.