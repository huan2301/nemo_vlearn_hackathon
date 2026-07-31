# Reflection Cá Nhân — Hackathon AI Batch 03

- **Họ và tên:** Lê Đình Việt
- **Mã học viên:** 2A202601528
- **Nhóm:** Nemo VLearn
- **Vai trò:** Product Owner
- **Phụ trách chính:** chốt lát cắt, khai thác evidence, viết AI Spec, xác định quality bar, chuẩn hóa câu chuyện sản phẩm và phối hợp kiểm thử/demo.
- **Tỷ lệ đóng góp:** 25%

---

## 1. Công việc thực tế đã thực hiện

Trong hackathon, tôi chịu trách nhiệm kết nối bài toán người dùng, bằng chứng và bản prototype thành một câu chuyện sản phẩm thống nhất.

### 1.1. Xác định người dùng, pain và JTBD

Tôi xác định job executor chính là học viên mới học AI hoặc có nền tảng non-tech đang đọc slide trên VLearn. Core JTBD được chốt là:

> **Kiểm tra và củng cố ngay mức hiểu của mình về một thuật ngữ trong lúc đọc slide để tiếp tục bài học mà không tích lũy lỗ hổng kiến thức.**

Tôi tách nhu cầu thật của người học khỏi giải pháp. Người học không đơn thuần muốn “dùng AI giải thích thuật ngữ”, mà muốn biết mình đã hiểu đủ để tiếp tục bài học hay chưa.

### 1.2. Khai thác evidence từ dữ liệu VLearn

Tôi đọc data dictionary và sử dụng chatlog đã ẩn danh để xác định nhu cầu giải thích thuật ngữ. Quy tắc mining tập trung vào các lượt người học chọn đoạn ngắn và hỏi “là gì”, “nghĩa”, “giải thích” hoặc “dịch nghĩa”.

Kết quả được đưa vào `spec.md`:

- 281/1.261 lượt hỏi, tương đương **22,3%**, là yêu cầu giải thích đoạn ngắn.
- 132/369 người dùng, tương đương **35,8%**, từng phát sinh nhu cầu này.
- 66/281 câu trả lời, tương đương **23,5%**, không có citation.
- Chỉ 3/2.515 tutor message có hành vi đặt câu hỏi kiểm tra hiểu.
- Các trường `follow_ups` và `misconceptions` gần như chưa được sử dụng.

Tôi cũng lưu các ví dụ có mã turn như `T0990`, `T1087`, `T0573`, `T0750`, `T0234` để số liệu có thể được kiểm tra lại, thay vì chỉ ghi nhận bằng cảm nhận cá nhân.

### 1.3. Viết và điều chỉnh AI Spec

Tôi trực tiếp xây dựng và cập nhật `spec.md` theo template của chương trình, gồm:

- User, JTBD, problem statement và evidence.
- Bảng impact và lý do chọn bài toán.
- Lát cắt prototype theo format một user, một việc, một quyết định AI và một kết quả.
- Phân biệt phần VLearn Tutor đã có, phần tối ưu lõi và phần roadmap.
- Non-goals, mức automation và cost of error.
- Các nguyên tắc HAX/PAIR.
- Bốn lớp chỗ khó, các kịch bản lỗi và bốn đường đi trải nghiệm.
- Cấu trúc golden set và quality bar.
- Phân công, kế hoạch validation và changelog.

Sau khi nhóm thống nhất đây là sản phẩm tối ưu VLearn Tutor hiện có, tôi chuyển spec từ **Hướng C — Làn mở** sang **Hướng A — VLearn**. Product vision được mở rộng thành:

```text
Phát hiện thuật ngữ khó
→ giải thích theo ngữ cảnh và trình độ
→ chọn cách học
→ kiểm tra hiểu
→ cập nhật Learning Profile
→ tạo flashcard
→ xếp lịch ôn tập
```

Để tránh scope quá lớn, tôi giữ lát cắt demo ở một thuật ngữ và một quyết định AI trung tâm: chọn gói giải thích phù hợp dựa trên ngữ cảnh và Learning Profile.

### 1.4. Quality bar và phối hợp kiểm thử

Tôi đề xuất quality bar định lượng:

> Đạt khi ít nhất 85% golden cases qua trọn bộ, đồng thời các case an toàn, acronym, citation và cập nhật profile phải đạt các điều kiện cứng.

Tôi phối hợp với các thành viên để đối chiếu spec với backend, frontend và eval; kiểm tra các chức năng health, session, giải thích thuật ngữ, lưu từ, chat và fallback. Tôi cũng chạy thử backend/frontend sau khi merge code mới và xác nhận lời gọi Groq thật sử dụng model `llama-3.3-70b-versatile`.

### 1.5. Câu chuyện sản phẩm và chuẩn bị demo

Tôi chuẩn hóa câu chuyện trình bày theo chuỗi:

```text
Bằng chứng
→ khoảng trống của Tutor hiện tại
→ quyết định chọn bài toán
→ Adaptive Glossary Learning Loop
→ một lát cắt demo
→ quality bar và rủi ro
```

Thông điệp tôi muốn giữ xuyên suốt là:

> VLearn Tutor không chỉ trả lời “RAG là gì?”, mà giúp người học biết “Tôi đã hiểu RAG chưa, và khi nào cần ôn lại?”.

---

## 2. AI đã hỗ trợ tôi như thế nào?

Tôi sử dụng AI như một công cụ hỗ trợ phân tích và kiểm tra, không giao toàn bộ quyết định sản phẩm cho AI.

AI hỗ trợ tôi ở các phần:

1. **Đọc và hệ thống hóa tài liệu:** đối chiếu đề bài, guide, template, rubric và codebase để lập checklist những phần spec bắt buộc.
2. **Mining dữ liệu:** hỗ trợ viết script lọc chatlog theo quy tắc do tôi xác định, đếm số lượt/người dùng và trích các `turn_id` để kiểm lại.
3. **Soát cấu trúc spec:** kiểm tra số lượng non-goals, nguyên tắc HAX/PAIR, kịch bản rủi ro và các section §1–§9.
4. **Diễn đạt và rút gọn:** hỗ trợ chuyển nội dung dài trong spec thành câu chuyện sáu slide và elevator pitch.
5. **Hỗ trợ kỹ thuật Git:** đọc trạng thái branch, phát hiện conflict `.gitignore`, commit nhầm `.venv`, hỗ trợ cleanup và đồng bộ với `main`.
6. **Kiểm tra prototype:** hỗ trợ chạy unit test, health check và một request giải thích `RAG` bằng Groq thật.

Các quyết định tôi trực tiếp chịu trách nhiệm gồm: chọn Hướng A, xác định JTBD, chọn lát cắt, quyết định Conditional Automation, đặt quality bar và phân biệt phần build thật với roadmap. Tôi kiểm tra lại số liệu và artifact trong repo trước khi đưa vào spec.

---

## 3. Case fail của nhóm và bài học rút ra

### 3.1. Chọn sai hướng sản phẩm ở giai đoạn đầu

Ban đầu, Canvas và bản spec đầu tiên mô tả AI Glossary Tutor là **Hướng C — Làn mở, tính năng mới**. Tuy nhiên, khi đối chiếu lại đề bài và codebase, tôi nhận ra VLearn Tutor đã có sẵn flow bôi đen, giải thích theo ngữ cảnh, session và lưu thuật ngữ. Nhóm thực tế đang tối ưu một sản phẩm hiện hữu, nên hướng đúng phải là **Hướng A — VLearn**.

Nếu giữ Hướng C, câu chuyện sản phẩm sẽ không khớp với artifact và nhóm có nguy cơ bị đánh giá sai ở phần lát cắt và prototype.

**Cách xử lý:** tôi viết lại spec theo Hướng A, lập bảng “phần cũ đã có/phần tối ưu”, giữ toàn bộ adaptive loop ở mức product vision nhưng khóa demo vào một quyết định AI trung tâm.

**Bài học:** trước khi mở rộng giải pháp, phải kiểm kê năng lực của sản phẩm hiện tại và xác định chính xác mình đang build mới hay tối ưu. Một câu chuyện hay nhưng không khớp code vẫn là một spec yếu.

### 3.2. Commit nhầm môi trường ảo `.venv`

Trong quá trình tạo môi trường chạy local, `.venv` chưa được ignore đúng thời điểm và hàng nghìn file dependency đã bị Git theo dõi. Việc này khiến phần compare với `main` xuất hiện rất nhiều file không liên quan và làm quy trình merge trở nên khó kiểm soát.

**Cách xử lý:** nhóm thêm `.venv/` vào `.gitignore`, dùng `git rm -r --cached .venv` để bỏ file khỏi Git nhưng giữ môi trường trên máy, sau đó kiểm tra lại diff trước khi merge.

**Bài học:** trước mỗi commit/PR phải chạy tối thiểu:

```powershell
git status
git diff --stat
git diff --name-status origin/main...HEAD
```

Không nên chỉ nhìn commit message hoặc số file trong working tree. Cần kiểm tra chính xác những gì sẽ đi vào `main`.

---

## 4. Bài học về thiết kế sản phẩm AI

1. **Evidence phải kiểm lại được:** “nhiều học viên hỏi thuật ngữ” không đủ mạnh bằng 281 lượt, 132 người dùng và danh sách turn ID.
2. **Giải thích chưa đồng nghĩa với học:** Tutor trả lời đúng vẫn chưa chứng minh người học đã hiểu. Câu kiểm tra và tín hiệu sau câu trả lời mới khép kín vòng học.
3. **Một lát cắt tốt quan trọng hơn nhiều tính năng:** auto-detect, bốn learning modes, profile, flashcard và spaced repetition là vision; demo vẫn cần tập trung vào một thuật ngữ và một quyết định AI.
4. **Không chắc thì hỏi lại:** với người mới, giải thích sai có cost of error cao vì họ khó tự phát hiện. Vì vậy Conditional Automation phù hợp hơn tự động hóa hoàn toàn.
5. **Spec phải phản ánh đúng code:** phần nào chưa build phải ghi Mock/Roadmap, không được mô tả như đã hoàn thành.
6. **Quality bar phải được đặt trước khi xem kết quả:** nếu thay bar theo kết quả, eval mất ý nghĩa.

---

## 5. Tự đánh giá

Tôi đã hoàn thành phần Product Owner được phân công: chốt lại hướng sản phẩm, khai thác evidence, xây dựng AI Spec, xác định lát cắt và quality bar, đồng thời phối hợp kiểm tra prototype và chuẩn hóa câu chuyện demo.

Điểm tôi làm tốt nhất là chuyển một ý tưởng nhiều tính năng thành một chuỗi quyết định có bằng chứng và giới hạn rõ ràng. Điểm tôi cần cải thiện là phải chốt đúng hướng và kiểm tra trạng thái repository sớm hơn, tránh phải sửa lớn vào giai đoạn sau.

Tôi có thể giải thích các phần mình phụ trách, bao gồm:

- Cách viết JTBD và problem statement.
- Phương pháp mining 281 lượt hỏi.
- Vì sao chọn Hướng A.
- Vì sao lát cắt chỉ giữ một quyết định AI.
- Vì sao chọn Conditional Automation.
- Cách đặt quality bar 85%.
- Sự khác nhau giữa product vision, prototype thật và roadmap.

