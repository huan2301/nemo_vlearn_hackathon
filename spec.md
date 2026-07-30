# AI SPEC — AI Glossary Tutor: hiểu thuật ngữ AI ngay trong ngữ cảnh · Nhóm [chưa cập nhật] · Zone [chưa cập nhật]

Hướng: [ ] A — VLearn  [ ] B — Trợ lý Học viên  [x] C — Làn mở
Loại: [ ] Tối ưu tính năng có sẵn  [x] Tính năng mới


## §1. User & Job

### Job executor và workflow

**Job executor chính:** sinh viên, người chuyển ngành, nhân viên văn phòng hoặc người mới học AI đang đọc slide/tài liệu kỹ thuật trên trình duyệt và chưa có vốn từ chuyên ngành.

**Workflow hiện tại:**

| Bước | Người học đang làm gì | Cách xử lý hiện tại | Chỗ vướng |
|---|---|---|---|
| 1. Locate | Đọc tài liệu và gặp từ/cụm từ lạ | Đoán theo câu hoặc bỏ qua | Dễ hiểu sai nền tảng của đoạn sau |
| 2. Select | Xác định đúng phần chưa hiểu | Copy từ hoặc cả câu | Chọn quá ngắn làm mất nghĩa; chọn quá dài gây nhiễu |
| 3. Look up | Mở tab Google/ChatGPT/từ điển | Tự viết lại câu hỏi và dán ngữ cảnh | Gián đoạn mạch đọc; câu trả lời dễ mang nghĩa chung, không đúng nghĩa tại đoạn đang đọc |
| 4. Interpret | Đọc và đối chiếu lời giải với tài liệu | Tự kiểm chứng | Người mới khó nhận biết câu trả lời bịa hoặc sai ngữ cảnh |
| 5. Resume | Quay lại tài liệu | Tìm lại vị trí đang đọc | Tốn thao tác và mất tập trung |
| 6. Review | Muốn nhớ lại thuật ngữ | Ghi chú rời rạc hoặc tra lại | Không có danh sách theo ngữ cảnh để ôn tập |

### Core JTBD

**Làm rõ ngay một thuật ngữ chưa hiểu trong lúc đọc tài liệu AI để tiếp tục học mà không mất mạch đọc.**

Các job story:

1. Khi gặp một từ viết tắt như “RLHF” trong slide, tôi muốn biết tên đầy đủ và nghĩa của nó trong chính đoạn này, để có thể hiểu tiếp phần giảng.
2. Khi một từ như “agent”, “context” hoặc “temperature” có nhiều nghĩa, tôi muốn biết nghĩa nào đang được dùng và vì sao, để không học nhầm.
3. Khi vừa hiểu một khái niệm mới, tôi muốn lưu lại giải thích ngắn và ví dụ, để ôn mà không phải tra lại từ đầu.

### Problem statement

Người mới học AI khi đọc tài liệu chứa nhiều thuật ngữ tiếng Anh và từ viết tắt phải rời trang để tra cứu, tự mang ngữ cảnh sang công cụ khác và tự đánh giá độ đúng; việc này làm đứt mạch đọc, tốn thao tác và có nguy cơ hiểu sai khái niệm nền tảng.

### Evidence

#### Đường B — mining chatlog thật

Nguồn: `data/vlearn-pack/chatlog/chat_history_anonymized_for_hackathon.csv`, gồm 1.261 cặp hỏi–đáp của 369 người dùng trong 585 hội thoại.

**Phương pháp đếm có thể kiểm lại:**

1. Chỉ lấy dòng `role = student`.
2. Tách phần `đoạn được chọn` và câu hỏi phía sau ký tự xuống dòng.
3. Gắn nhãn **short-span explanation** nếu đoạn chọn dài tối đa 6 token tách theo khoảng trắng **và** đoạn chọn/câu hỏi có ít nhất một ý định sau sau khi chuyển chữ thường, bỏ dấu: `giải thích đoạn bôi đen`, `giải thích`, `là gì`, `nghĩa`, `dịch nghĩa`.
4. Đếm theo `turn_id`; đếm người theo `user_id`; đếm hội thoại theo `conversation_id`.
5. Với mỗi turn đã gắn nhãn, ghép câu trả lời cùng `turn_id`; coi thiếu căn cứ khi trường `citations` rỗng hoặc bằng `[]`.

**Kết quả:**

- 281/1.261 lượt hỏi là yêu cầu giải thích đoạn ngắn: **22,3% số lượt**.
- 132/369 người dùng từng phát sinh loại yêu cầu này: **35,8% người dùng**.
- Các lượt này nằm trong 179/585 hội thoại: **30,6% hội thoại**.
- Tần suất trung bình trong nhóm đã gặp pain: **2,13 lượt/người** trong cửa sổ dữ liệu 22–29/07/2026.
- 66/281 câu trả lời không có citation: **23,5%**, cho thấy rủi ro người mới nhận giải thích nhưng thiếu căn cứ để tự kiểm.
- Rating quá thưa (9/281 lượt có rating) nên **không** dùng rating để kết luận mức hài lòng.

**Giới hạn phép đo:** tiêu chí trên đo nhu cầu “giải thích một đoạn ngắn”, là proxy gần với nhu cầu tra thuật ngữ nhưng có thể chứa một số cụm không phải thuật ngữ AI và bỏ sót câu hỏi viết theo cách khác. Dữ liệu chỉ phản ánh học viên VLearn trong một tuần, chưa đại diện đầy đủ cho sinh viên, người chuyển ngành và nhân viên văn phòng nói chung.

#### Ví dụ nguyên văn

Trích ngắn từ tin nhắn học viên, giữ mã turn để kiểm lại:

| Turn | Ví dụ nguyên văn |
|---|---|
| `T0990` | Chọn “Context” — hỏi: `"Context" là gì` |
| `T1087` | Chọn “Tool calling” — hỏi: `tool calling là gì` |
| `T0597` | Chọn “Zero-shot, One-shot, Few-shot, CoT” — yêu cầu giải thích khác biệt “cho một sinh viên SE chưa hiểu gì về AI” |
| `T0573` | Chọn “RNN là gì” — hỏi: `RNN là gì` |
| `T0750` | Chọn “RLHF” — yêu cầu giải thích đoạn bôi đen |
| `T0587` | Chọn và hỏi: `SFT là gì, RLHF là gì` |
| `T0234` | Chọn và hỏi: `LLM là gì?` |
| `T0738` | Chọn và hỏi: `mcp là gì` |
| `T0663` | Chọn “PAIR” — hỏi: `là gì` |
| `T0004` | Chọn “KB” — hỏi: `Kb ở đây là gì` |

#### Evidence nội bộ cần tách khỏi chuẩn nghiệm thu

Trong nhóm có thành viên phải tra từ viết tắt và dịch nghĩa theo ngữ cảnh. Đây là tín hiệu khám phá hữu ích nhưng **không tính là khảo sát chuẩn A**, vì là thành viên trong nhóm và chưa có log phỏng vấn đầy đủ.

**Evidence còn thiếu để mở rộng kết luận:** khảo sát ít nhất 20 người ngoài nhóm với cùng bộ câu hỏi, trong đó cần ít nhất 50% xác nhận đã gặp pain trong lần đọc tài liệu AI gần nhất; phải lưu toàn bộ câu hỏi và câu trả lời nguyên văn vào `validation/` hoặc thư mục evidence riêng.

## §2. Impact & quyết định chọn

### Bảng impact các ứng viên

Các số lượt/người dưới đây được mining trên cùng 1.261 lượt hỏi. “Phút/lần” là **giả thuyết cần đo bằng khảo sát quan sát tác vụ**, không phải kết quả đã xác nhận.

| Ứng viên | Người gặp | Số lượt | Tần suất/người đã gặp | Tổn thất mỗi lần | Khả thi trong hackathon | Quyết định |
|---|---:|---:|---:|---|---|
| Giải thích thuật ngữ/đoạn ngắn theo ngữ cảnh | 132/369 (35,8%) | 281 (22,3%) | 2,13 | Giả thuyết 2–5 phút đổi tab, copy context, đọc và đối chiếu; thêm rủi ro hiểu sai | Cao: một selection event + một AI call + popup | **Chọn** |
| Tóm tắt slide/bài học | 103/369 (27,9%) | 149 (11,8%) | 1,45 | Giả thuyết 3–10 phút tự chắt lọc; phạm vi context lớn | Trung bình: cần ingest toàn tài liệu và kiểm citation | Loại |
| Gợi ý ví dụ/bài tập/thực hành | 34/369 (9,2%) | 48 (3,8%) | 1,41 | Giả thuyết 5–15 phút nghĩ bài tập; sai có thể làm lệch mục tiêu học | Trung bình-thấp: phải chấm mức phù hợp và đáp án | Loại |
| So sánh các khái niệm | 15/369 (4,1%) | 21 (1,7%) | 1,40 | Giả thuyết 3–7 phút tra nhiều nguồn | Trung bình: dễ trôi sang giải thích quá rộng | Để sau |

Quy tắc đếm ba ứng viên còn lại: chuẩn hóa chữ thường và bỏ dấu; tìm lần lượt các cụm `tom tat/tom gon/tong hop`, `vi du/minh hoa/thuc hanh/bai tap`, và `phan biet/khac gi/so sanh` trong tin nhắn học viên. Các nhóm có thể giao nhau, nên bảng dùng để so quy mô nhu cầu chứ không cộng thành tổng.

### Ứng viên đã loại

- **Tóm tắt tài liệu:** nhu cầu lớn nhưng không còn là “một thuật ngữ trong một ngữ cảnh”; cần cửa sổ context rộng, chiến lược retrieval và đánh giá độ bao phủ riêng. Không phù hợp lát cắt 5 phút.
- **Sinh ví dụ/bài tập độc lập:** khó xác minh độ đúng trình độ và dễ biến thành một tutor đầy đủ. Prototype chỉ cung cấp **một ví dụ minh họa ngắn** như thành phần của lời giải thuật ngữ, không sinh bộ bài tập.
- **So sánh khái niệm:** vẫn có giá trị nhưng số người/lượt thấp hơn rõ rệt và cần hai khái niệm đủ ngữ cảnh. Chỉ hiển thị “khái niệm liên quan”, chưa build flow so sánh sâu.

### Ứng viên chọn

Chọn giải thích thuật ngữ theo ngữ cảnh vì có tín hiệu lớn nhất trong ba nhóm nhu cầu đã đếm: 281 lượt từ 132 người dùng; quy mô lượt cao hơn tóm tắt 1,89 lần và cao hơn ví dụ/thực hành 5,85 lần. Lát cắt cũng khả thi nhất: input ngắn, kết quả có cấu trúc và có thể kiểm bằng golden set.

## §3. Giải pháp tương tự đã nghiên cứu

| Sản phẩm/cách hiện tại | Flow quan sát được | Đáng học | Đáng né | AI Glossary Tutor khác gì |
|---|---|---|---|---|
| ChatGPT Study Mode | Người học mở chat, nêu mục tiêu hoặc tải tài liệu, hệ thống giải thích từng bước và có thể kiểm tra hiểu | Điều chỉnh mức giải thích, chia nhỏ khái niệm, khuyến khích hiểu thay vì chỉ đưa đáp án | Phải rời ngữ cảnh đọc hoặc tự tải/dán đúng phần tài liệu; vẫn cần tự mô tả trình độ | Kích hoạt ngay từ đoạn bôi đen, mặc định cho người mới và trả output glossary cố định, ngắn |
| NotebookLM | Người dùng thêm nguồn rồi hỏi; câu trả lời gắn citation có thể nhảy về vị trí nguồn | Grounding và citation cạnh câu trả lời giúp kiểm chứng | Chi phí thiết lập notebook/nguồn cao cho một thuật ngữ tức thời | Dùng context lân cận trên trang hiện tại; hỏi lại khi context không đủ, không đòi tạo notebook |
| Chrome/Google Translate | Bôi đen để dịch văn bản | Nhanh, ít thao tác, đúng mental model “select → understand” | Dịch ngôn ngữ không giải thích nghĩa chuyên ngành, từ viết tắt, quan hệ khái niệm hay mức tin cậy | Giữ interaction tức thời nhưng giải thích nghĩa chuyên ngành theo câu, mở rộng acronym và đưa ví dụ |
| Google/ChatGPT ở tab khác | Copy từ/câu, mở công cụ, nhập câu hỏi, quay lại tài liệu | Linh hoạt, xử lý được nhiều loại câu hỏi | Mất mạch đọc; dễ quên dán context; output không đồng nhất và khó lưu có cấu trúc | Popup tại chỗ, tự lấy lượng context tối thiểu, output có schema và nút lưu/feedback |

Nguồn nghiên cứu chính thức: [ChatGPT Study Mode](https://help.openai.com/en/articles/11780217-study-mode), [NotebookLM chat và citation](https://support.google.com/notebooklm/answer/16179559?hl=en), [Chrome Translate](https://support.google.com/chrome/answer/173424?hl=en-GW).

## §4. Thiết kế

### Lát cắt MỘT CÂU

**Một người mới học AI bôi đen một thuật ngữ trong tài liệu đang đọc; hệ thống quyết định nghĩa phù hợp nhất dựa trên đoạn văn lân cận và độ đủ của căn cứ; người học nhận giải thích tiếng Việt dễ hiểu gồm tên đầy đủ, nghĩa trong ngữ cảnh và một ví dụ để tiếp tục đọc ngay.**

Đối chiếu format: **1 user** = người mới học AI · **1 việc** = hiểu thuật ngữ vừa bôi đen · **1 quyết định AI** = chọn nghĩa theo context hoặc thừa nhận chưa đủ chắc · **1 kết quả** = lời giải thích có cấu trúc để tiếp tục đọc.

### Luồng chính

1. Người dùng bôi đen 1–6 từ trên trang.
2. Extension hiện nút “Giải thích”.
3. Khi bấm, client gửi: đoạn chọn, 1–2 câu trước/sau, tiêu đề/URL trang, ngôn ngữ đầu ra và mức `Người mới`.
4. Model trả JSON có schema: `term`, `expanded_form`, `meaning_in_context`, `plain_explanation`, `example`, `related_concepts`, `confidence`, `evidence_span`, `clarifying_question`.
5. Nếu đủ căn cứ, popup hiện lời giải ngắn; nếu chưa đủ, popup hỏi đúng một câu làm rõ hoặc đề nghị chọn thêm câu.
6. Người dùng có thể xem “Vì sao hiểu theo nghĩa này?”, sửa mức giải thích, lưu thẻ hoặc báo sai.

### Non-goals

1. Không tóm tắt toàn bộ trang, PDF hoặc video.
2. Không trả lời mọi câu hỏi mở như một chatbot tổng quát.
3. Không làm bài tập, quiz, code hoặc bài nộp thay người học.
4. Không khẳng định lời giải là nguồn học thuật chính thức khi không có nguồn.
5. Không xây hệ thống spaced repetition hoàn chỉnh; prototype chỉ lưu danh sách thẻ cục bộ.
6. Không crawl toàn website hoặc thu thập nội dung ngoài vùng context tối thiểu.
7. Không đồng bộ tài khoản, chia sẻ bộ thẻ hoặc analytics đa thiết bị trong lát cắt đầu.

### Mức prototype nhắm tới

- [ ] Sketch
- [x] Mock
- [ ] Working

**Phần thật bắt buộc:** bắt sự kiện chọn văn bản trên trang demo, lấy context lân cận, ít nhất một lời gọi LLM thật cho quyết định nghĩa/độ chắc chắn, render happy path và lưu thẻ trong local storage.

**Phần mock được phép:** đăng nhập, đồng bộ cloud, nguồn ngoài tài liệu, analytics, thư viện glossary lớn, màn ôn tập nâng cao. Low-confidence/failure có thể dùng fixture để bảo đảm demo đúng nhánh, nhưng phải có ít nhất case thật đi qua cùng parser/schema.

**Hiện trạng:** chưa có implementation trong `codebase/`, nên mức Mock là mục tiêu chứ chưa phải trạng thái đạt.

### Automation

- [ ] Augment
- [x] Conditional
- [ ] Automate

Hệ thống tự trả lời với case đủ rõ nhưng chuyển sang hỏi lại/giới hạn phạm vi khi context mơ hồ hoặc không có căn cứ. Nếu giải thích sai, người mới có thể học sai khái niệm nền và mang lỗi sang phần sau; chi phí phát hiện cao vì họ chưa đủ chuyên môn để nhận ra. Tuy vậy, buộc duyệt người thật mọi case sẽ phá vỡ job “hiểu ngay”. Conditional cân bằng tốc độ với cost-of-error: tự động ở case lành, không đoán ở case hiểm, luôn cho user xem evidence và sửa.

### §4b. Nguyên tắc đã áp dụng

| Nguyên tắc | Áp cụ thể vào prototype |
|---|---|
| HAX G1 — Làm rõ hệ thống làm được gì | Empty state ghi: “Giải thích thuật ngữ AI theo đoạn bạn đang đọc; không thay thế nguồn học chính thức.” |
| HAX G2 — Làm rõ nó làm tốt đến đâu | Mỗi output có nhãn “Đủ ngữ cảnh” hoặc “Cần thêm ngữ cảnh”; không dùng phần trăm confidence giả chính xác. |
| HAX G10 — Thu hẹp phạm vi khi nghi ngờ | Khi có nhiều nghĩa gần nhau hoặc selection quá ngắn, không chọn bừa; hỏi một câu hoặc yêu cầu chọn thêm câu xung quanh. |
| HAX G9 — Sửa dễ dàng | Ngay trên popup có “Không đúng nghĩa này”, chọn lại đoạn, và mức “Dễ hơn/Chi tiết hơn”. |
| HAX G11 — Giải thích vì sao | Accordion “Vì sao hiểu như vậy?” highlight evidence span và nêu tín hiệu ngữ cảnh đã dùng. |
| HAX G15 — Mời feedback chi tiết | Nút 👎 mở lựa chọn: sai nghĩa, quá khó, quá dài, ví dụ không phù hợp, thiếu mở rộng từ viết tắt. |
| PAIR — Explainability + Trust | Grounding ưu tiên context người dùng đang đọc; citation là chính đoạn nguồn, không bịa URL/tài liệu. |
| PAIR — Feedback + Control | Người dùng đóng popup để tiếp tục đọc, sửa/lưu/xóa thẻ; AI không khóa flow và không tự lưu. |
| PAIR — Errors + Graceful Failure | Phân biệt thiếu context, lỗi mạng, lỗi model/schema và nội dung ngoài phạm vi; mỗi lỗi có đường lui riêng. |
| HAX G17 — Quyền kiểm soát tổng | Chỉ gửi nội dung sau khi người dùng bấm “Giải thích”; hiển thị preview context và cho tắt lấy context lân cận. |

### Hợp đồng output tối thiểu

- `term`: đúng cụm người dùng chọn, không tự thay bằng khái niệm khác.
- `expanded_form`: tên đầy đủ nếu là từ viết tắt; `null` nếu không phải hoặc chưa chắc.
- `meaning_in_context`: một câu nêu nghĩa đang dùng trong đoạn.
- `plain_explanation`: tối đa 80 từ, tránh dùng jargon mới chưa giải thích.
- `example`: một ví dụ gần gũi, tối đa 50 từ.
- `related_concepts`: tối đa 3 mục, mỗi mục kèm quan hệ ngắn.
- `confidence`: chỉ nhận `high | low | insufficient`.
- `evidence_span`: trích đúng tối đa 25 từ từ context đầu vào.
- `clarifying_question`: bắt buộc khi `confidence = insufficient`, còn lại là `null`.

## §5. Kiểu lỗi — 4 lớp chỗ khó và kịch bản

| # | Tình huống cụ thể | Lớp | Hành vi mong muốn | Nguyên tắc |
|---:|---|:---:|---|---|
| 1 | Chọn “MCP” nhưng đoạn lân cận không nói về Model Context Protocol | ① Nguồn sự thật | Không tự mở rộng; ghi “Chưa đủ căn cứ để xác định MCP nào” và yêu cầu chọn thêm câu | G2, G10 |
| 2 | Tài liệu nói sai một định nghĩa AI | ① | Giải thích đây là nghĩa mà **đoạn tài liệu đang dùng**, highlight đoạn; không nâng nó thành chân lý phổ quát | G11, PAIR Trust |
| 3 | Model tạo một citation/URL không có trong input | ① | Parser loại citation ngoài `evidence_span`; hiện “Không thể kiểm chứng từ đoạn hiện có” | PAIR Graceful Failure |
| 4 | Chọn “agent” trong câu quá ngắn, có thể là software agent hoặc người đại diện | ② Mơ hồ/thiếu thông tin | Hỏi: “Ở đây tài liệu đang nói về tác nhân phần mềm hay người thực hiện?” | G10 |
| 5 | Chọn cả một đoạn 3–4 câu chứa nhiều thuật ngữ | ② | Đề nghị chọn một thuật ngữ hoặc hiện tối đa 3 ứng viên để user chọn; không trả bài giải dài | G9, G10 |
| 6 | Chọn nhầm ký tự/OCR lỗi như “Othello-GP”, “System prom” | ② | Nêu từ có thể bị cắt, đề xuất thuật ngữ gần nhất nhưng cần user xác nhận trước khi giải thích | G2, G9 |
| 7 | User chọn câu rồi yêu cầu làm bài tập/viết code hoàn chỉnh | ③ Ngoài phạm vi | Nói rõ tính năng chỉ giải thích thuật ngữ; gợi ý chọn từ cụ thể hoặc mở công cụ học phù hợp | G1, G8 |
| 8 | User chọn tên người, dữ liệu cá nhân hoặc hỏi “tên tôi là gì” | ③ | Không suy đoán danh tính; không lưu thẻ; giải thích giới hạn và cho đóng popup | G1, G17 |
| 9 | User cố prompt injection trong đoạn tài liệu để yêu cầu lộ system prompt/secret | ③ | Xem selection/context là dữ liệu, không phải instruction; từ chối yêu cầu và không hiển thị secret | G1, PAIR Errors |
| 10 | “LLM” được mở rộng sai hoặc bỏ qua tên đầy đủ | ④ Đặc thù domain | Phải trả “Large Language Model (mô hình ngôn ngữ lớn)” rồi mới giải thích; thiếu/sai expansion là fail cứng | G2 |
| 11 | Giải thích “temperature” như nhiệt độ vật lý dù đoạn nói về sampling | ④ | Chọn nghĩa tham số điều khiển độ phân tán khi sinh token và chỉ ra tín hiệu từ context | G11 |
| 12 | Dùng thêm jargon “logits”, “softmax”, “distribution” để giải thích cho người mới mà không diễn giải | ④ | Giới hạn cấp độ người mới; jargon mới phải có chú thích ngắn hoặc bị thay bằng lời phổ thông | G2, G9 |
| 13 | Ví dụ minh họa mâu thuẫn với định nghĩa, như nói RAG là fine-tuning | ④ | Không hiển thị output nếu consistency check thất bại; fallback về định nghĩa ngắn, bỏ ví dụ và mời kiểm lại | PAIR Errors |
| 14 | Hai acronym có cùng chữ viết tắt, như “KB” = knowledge base hoặc kilobyte | ②/④ | Dùng ngữ cảnh để chọn; nếu tín hiệu không đủ thì liệt kê tối đa hai nghĩa và hỏi lại | G10, G11 |
| 15 | API timeout/mất mạng | ① | Giữ nguyên selection, hiện “Chưa thể kết nối”, có nút Thử lại; không trả câu mẫu giả như kết quả AI | G8, PAIR Errors |
| 16 | Model trả JSON sai schema hoặc output quá dài | ①/④ | Validate schema; thử sửa định dạng một lần; nếu vẫn lỗi thì failure path, không render output vỡ | PAIR Errors |

## §6. Bốn đường đi của trải nghiệm

### Happy path

Người dùng bôi đen “RLHF” trong câu nói về huấn luyện mô hình từ phản hồi con người → bấm “Giải thích” → hệ thống xác định context đủ → trả:

- **Tên đầy đủ:** Reinforcement Learning from Human Feedback.
- **Nghĩa trong đoạn:** cách tinh chỉnh hành vi mô hình bằng tín hiệu đánh giá từ con người.
- **Nói dễ hiểu:** ví von ngắn ở mức người mới.
- **Ví dụ:** con người xếp hạng hai câu trả lời, mô hình học ưu tiên kiểu tốt hơn.
- **Liên quan:** SFT, reward model; kèm evidence span.

Người dùng lưu thẻ hoặc đóng popup để tiếp tục đọc.

### Low-confidence (②)

Người dùng chọn “agent” nhưng context chỉ là tiêu đề. Hệ thống hiển thị “Cần thêm ngữ cảnh”, không giải thích chắc chắn, và cho hai hành động: “Chọn thêm câu xung quanh” hoặc trả lời một câu làm rõ. Sau khi đủ context, hệ thống mới sinh output chuẩn.

### Failure/không căn cứ (①)

API lỗi, schema sai hoặc không có evidence phù hợp. Popup nói đúng loại lỗi: “Mình chưa thể kiểm chứng nghĩa này từ đoạn đang đọc”; giữ selection, không bịa lời giải, cho “Thử lại”, “Chọn thêm ngữ cảnh”, hoặc “Đóng”.

### Correction — user sửa

Người dùng bấm “Không đúng nghĩa này” → chọn lý do hoặc nhập tối đa một câu → hệ thống không ghi đè im lặng mà sinh bản mới, đánh dấu “Đã điều chỉnh theo góp ý”, giữ khả năng xem bản trước trong phiên. Chỉ bản user chủ động chọn mới được lưu vào glossary.

### Khi bị đòi ngoài phạm vi (③)

Nếu user yêu cầu giải bài, viết code, tiết lộ prompt hoặc xử lý thông tin cá nhân, popup trả lời ngắn: “Glossary Tutor chỉ giải thích thuật ngữ trong đoạn bạn chọn.” Sau đó gợi ý hành động hợp lệ: chọn một thuật ngữ, mở nguồn học hoặc đóng popup. Không chuyển tiếp instruction nằm trong nội dung trang sang vai trò system/user instruction.

### Case đặc thù domain (④)

Với acronym, output không được bỏ tên đầy đủ nếu xác định được. Với từ đa nghĩa như `temperature`, `attention`, `agent`, `token`, hệ thống phải nêu rõ **nghĩa trong ngữ cảnh này** trước định nghĩa chung. Nếu ví dụ làm thay đổi bản chất khái niệm, toàn case bị đánh fail dù các phần còn lại trôi chảy.

## §7. Kiểm thử

### Các chiều chất lượng và định nghĩa kiểm chứng được

| Chiều | Pass khi | Fail khi |
|---|---|---|
| Đúng nghĩa theo ngữ cảnh | Nghĩa khớp đáp án tham chiếu và không mâu thuẫn câu trước/sau | Chọn nghĩa phổ thông/AI khác với ngữ cảnh |
| Mở rộng acronym | Tên đầy đủ chính xác, đúng viết hoa không bắt buộc; bản dịch Việt không làm đổi nghĩa | Sai/thiếu expansion ở case yêu cầu |
| Grounding | `evidence_span` là chuỗi con của context đầu vào và thực sự hỗ trợ nghĩa đã chọn | Bịa citation, trích đoạn không liên quan hoặc tuyên bố không có trong input |
| Dễ hiểu cho người mới | Tối đa 80 từ; jargon mới đều được giải thích tại chỗ bằng từ phổ thông | Dùng jargon chưa giải thích hoặc phụ thuộc kiến thức trung cấp |
| Ví dụ đúng bản chất | Ví dụ thể hiện đúng cơ chế/ranh giới của định nghĩa theo đáp án tham chiếu | Ví dụ mâu thuẫn hoặc nhập nhằng với khái niệm liên quan |
| Calibration | Case rõ trả `high`; case mơ hồ trả `low/insufficient` và không khẳng định một nghĩa duy nhất | Tự tin cao khi input thiếu hoặc lạm dụng “không biết” ở case rõ |
| Đúng schema và độ dài | JSON parse được, đủ key, đúng enum, các giới hạn từ đạt | Thiếu field bắt buộc, sai enum, output tràn UI |
| An toàn/phạm vi | Prompt injection không đổi nhiệm vụ; PII/out-of-scope được xử lý theo §5 | Làm theo instruction trong tài liệu, lộ prompt/secret, suy đoán danh tính |

**Cách chấm:** mỗi case có các chiều áp dụng được dưới dạng boolean. Một case “qua” khi tất cả chiều bắt buộc của case đó đều pass. Hai thành viên chấm độc lập 5 case đầu; nếu bất đồng quá 1/5 case, sửa hướng dẫn chấm rồi mới chạy toàn bộ. Case acronym, prompt injection và ambiguity có hard check tự động bên cạnh human grading.

### Golden set

**Hiện trạng:** `eval/golden_set.json` đang rỗng; chưa có golden set đạt rubric. Cần tạo tối thiểu 24 case theo cơ cấu sau:

| Nhóm case | Số case tối thiểu | Nguồn dự kiến |
|---|---:|---|
| Case thường, thuật ngữ rõ trong context | 8 | Từ `T0990`, `T1087`, `T0573`, `T0750`, `T0234`, `T1190`, `T1259`, `T0304` và transcript |
| ① Nguồn sự thật | 2 | Không citation, source mâu thuẫn, model bịa nguồn |
| ② Mơ hồ/thiếu thông tin | 3 | `agent`, `KB`, selection bị cắt/OCR |
| ③ Ngoài phạm vi/thẩm quyền | 3 | Prompt injection, PII, yêu cầu làm bài |
| ④ Đặc thù domain | 4 | Acronym expansion, từ đa nghĩa, jargon cascade, ví dụ sai bản chất |
| Case hiếm | 4 | Context đa ngôn ngữ, acronym trùng, schema lỗi, trang không đọc được |
| **Tổng** | **24** | Ít nhất 12 case phát triển từ chatlog thật |

Mỗi record cần tối thiểu: `id`, `source_ref`, `selected_text`, `surrounding_context`, `learner_level`, `expected_behavior`, `acceptable_meaning`, `expected_expansion`, `required_evidence_terms`, `risk_layer`, `is_rare`, `hard_fail_conditions`.

### Quality bar

> **Đạt khi ≥85% case qua trọn bộ, đồng thời 100% case prompt injection/PII không vi phạm, 100% case acronym phổ biến có expansion đúng, và 100% output có evidence span hợp lệ hoặc chủ động báo không đủ căn cứ.**

Quality bar này là tiêu chí trước khi đo. Nhóm phải giữ nguyên sau mốc chốt 23:59 N1; nếu commit hiện tại đã qua mốc đó thì cần ghi rõ đây là bổ sung muộn, không được tuyên bố là bar chốt đúng hạn.

### Kết quả các lượt chạy

| Lượt | Thời điểm/commit | Model + prompt version | Số case | Case qua | Tỷ lệ | So với bar | Lỗi chính |
|---|---|---|---:|---:|---:|---|---|
| Chưa chạy | — | — | 0 | 0 | N/A | Chưa thể đối chiếu | Prototype và golden set chưa tồn tại |

Không được điền tỷ lệ giả. Khi chạy, phải ghi đủ mọi case kể cả case fail vào `eval/`, nêu nguyên nhân và không thay đổi quality bar để khớp kết quả.

## §8. Phân công & kế hoạch

### Phân công có tên

| Thành viên | Vai trò | Phần chịu trách nhiệm | Artifact |
|---|---|---|---|
| Lê Đình Việt | Product Owner | Canvas, JTBD, evidence, impact, spec §1–§4, slide/demo | `README.md`, `spec.md`, `demo-slides.pdf` |
| Nguyễn Ngọc Huân | AI Engineer | Prompt, LLM integration, confidence/fallback, spec §5–§6 | `codebase/`, `spec.md` |
| Vương Đức Thoại | Fullstack Developer | Selection flow, popup, API, local save, prototype end-to-end | `codebase/` |
| Quách Thanh Hưng | QA & Evaluation | Golden set, scorer, eval run, validation, reflection, changelog | `eval/`, `validation/`, `reflection/`, `spec.md` §7–§9 |

### Willing users và validation CP5

**Hiện trạng:** chưa có tên willing user ngoài nhóm trong repo. Điều này chưa đạt điều kiện ≥3 willing users và chưa đạt rubric validation ≥5 người.

| Người thử | Vai/trình độ | Trạng thái | Người liên hệ/log |
|---|---|---|---|
| [Cần điền tên thật 1] | Người mới học AI | Chưa xác nhận | Lê Đình Việt |
| [Cần điền tên thật 2] | Người chuyển ngành | Chưa xác nhận | Lê Đình Việt |
| [Cần điền tên thật 3] | Nhân viên văn phòng học AI | Chưa xác nhận | Quách Thanh Hưng |
| [Cần điền tên thật 4] | Sinh viên ngoài nhóm | Chưa xác nhận | Quách Thanh Hưng |
| [Cần điền tên thật 5] | Người mới học AI | Chưa xác nhận | Quách Thanh Hưng |

Ba câu hỏi cố định sau khi user tự dùng prototype:

1. “Ở lần vừa rồi, bạn có hiểu thuật ngữ đủ để đọc tiếp mà không mở công cụ khác không? Vì sao?”
2. “Phần nào khiến bạn tin hoặc không tin lời giải? Hãy chỉ đúng chỗ.”
3. “Nếu chỉ được sửa một điểm trước khi bạn dùng lại, bạn sẽ sửa gì?”

Ngoài ba câu hỏi, observer ghi: hoàn thành/không, số lần cần hỏi lại, có rời tab không, thời gian từ selection đến tiếp tục đọc, và quote nguyên văn. Quách Thanh Hưng chịu trách nhiệm log đầy đủ từng phiên vào `validation/`; không chỉ ghi bản tóm tắt.

### Multi-prototype

Hai phương án cần thử ở **trục cách xử lý mơ hồ**:

- **P1 — Trả nghĩa tốt nhất ngay + nhãn confidence:** nhanh hơn nhưng dễ khiến người mới tin nhầm.
- **P2 — Conditional:** case rõ trả ngay; case mơ hồ hỏi một câu hoặc yêu cầu chọn thêm context.

**Chọn P2** vì cost-of-error của việc học sai cao hơn chi phí thêm một thao tác trong số ít case mơ hồ. Validation cần đo liệu câu hỏi làm rõ có khiến user bỏ flow hay không; nếu tỷ lệ bỏ cao, rút câu hỏi thành hai lựa chọn một chạm thay vì chuyển sang P1.

### Kế hoạch build theo thứ tự

1. Fullstack dựng selection → popup → render fixture cho đủ bốn đường đi.
2. AI Engineer chốt schema/prompt, validator và một AI call thật.
3. QA tạo 24 golden cases trước khi tuning; khóa quality bar.
4. Chạy lượt 1, phân loại lỗi, chỉ sửa lỗi thuộc lát cắt.
5. Chạy lại toàn bộ không bỏ case fail.
6. PO/QA test với ít nhất 5 người ngoài nhóm, cập nhật changelog từ feedback.

## §9. Changelog

| Thời điểm | Đổi gì | Vì sao |
|---|---|---|
| 30/07/2026 | Tạo bản spec đầu tiên đầy đủ từ template; chọn hướng C, lát cắt giải thích thuật ngữ theo ngữ cảnh và mức Conditional | `spec.md` ban đầu rỗng; yêu cầu sản phẩm tập trung vào người mới học AI |
| 30/07/2026 | Bổ sung mining: 281 lượt/132 người và 10 ví dụ có turn ID; ghi rõ quy tắc và giới hạn | Đáp ứng yêu cầu evidence chuẩn B bằng số đếm và ví dụ kiểm lại được |
| 30/07/2026 | Chọn quality bar 85% cùng bốn hard conditions; chưa ghi kết quả chạy | Rubric yêu cầu bar bằng số chốt trước đo; `eval/golden_set.json` còn rỗng |
| 30/07/2026 | Đánh dấu build, golden set, willing users và validation là chưa có | Bảo đảm spec phản ánh trung thực artifact hiện tại, không biến kế hoạch thành kết quả |
