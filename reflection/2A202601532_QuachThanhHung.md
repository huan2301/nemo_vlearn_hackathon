# Reflection Cá Nhân — Hackathon AI Batch 03

- **Họ và tên:** Quách Thanh Hưng
- **Mã học viên:** 2A202601532
- **Nhóm:** Nemo vlearn
- **Phụ trách chính:** Thu thập thông tin người dùng; QA; xây dựng Golden Set, scorer, evaluation run và validation.
- **Tỷ lệ đóng góp:** 25%

---

## 1. Công việc thực tế đã triển khai

Trong suốt hackathon, tôi chịu trách nhiệm thu thập nhu cầu người dùng và xây dựng quy trình **QA/Evaluation** cho sản phẩm **Prototype AI Glossary Tutor cho VLearn**:

1. **Khảo sát và thu thập thông tin người dùng:**
   - Trực tiếp khảo sát, phỏng vấn người dùng thật và thu thập nhu cầu, mong muốn của khoảng 30 người dùng.
   - Tổng hợp các tình huống sử dụng và rủi ro thực tế làm đầu vào cho việc xác định yêu cầu sản phẩm và kiểm thử mô hình.

2. **Xây dựng Bộ Golden Set (`eval/golden_set.json`):**
   - Xây dựng 24 test case, bao phủ từ happy path đến các tình huống biên có thể phát sinh khi người dùng tương tác với AI.
   - Bao gồm prompt không rõ ràng, nguy cơ prompt injection, yêu cầu ngoài phạm vi thẩm quyền và các trường hợp mô hình cần phản hồi an toàn.

3. **Lập trình công cụ Evaluation và Validation:**
   - Xây dựng công cụ chạy test model theo hai phương pháp: đánh giá dựa trên rule và **LLM-as-a-Judge**.
   - Tự động hóa evaluation run, tổng hợp kết quả và validation để có tiêu chí đánh giá rõ ràng, minh bạch và có thể lặp lại giữa các lần cải tiến model.

---

## 2. Bài học kinh nghiệm & Quyết định thiết kế đáng chú ý

- **Bài học về QA:** Một bộ test tốt cần đa dạng về ngữ cảnh, mức độ rõ ràng của prompt và các tình huống biên, thay vì chỉ tập trung vào kết quả đúng ở happy path. Bên cạnh việc xây dựng test case, cần kiểm tra khả năng đánh giá của chính bộ test để bảo đảm kết quả evaluation phản ánh đúng chất lượng và mức độ an toàn của mô hình trong các tình huống phát sinh.
- **Quyết định đánh giá hai lớp:** Kết hợp rule-based evaluation với LLM-as-a-Judge để vừa kiểm tra được các tiêu chí xác định rõ ràng, vừa đánh giá được chất lượng phản hồi ở những tình huống cần xét ngữ nghĩa và ngữ cảnh.
- **Bài học phối hợp nhóm:** Việc thống nhất sớm yêu cầu, tiêu chí chất lượng và cách bàn giao với AI Engineer Nguyễn Ngọc Huân và Product Owner Lê Đình Việt giúp các thành viên phát triển, kiểm thử độc lập theo phần việc của mình mà vẫn đồng bộ với mục tiêu chung, bảo đảm chất lượng AI mà không làm giảm tiến độ dự án.

---

## 3. Tự đánh giá

Tôi đã hoàn thành 100% khối lượng công việc được giao đúng hạn. Phần evaluation có hướng dẫn tự động hóa và báo cáo minh bạch, giúp nhóm dễ theo dõi, kiểm chứng và cải tiến chất lượng model. Tôi sẵn sàng giải thích chi tiết từng dòng code và các quyết định kỹ thuật của mình trong buổi demo CP6.
