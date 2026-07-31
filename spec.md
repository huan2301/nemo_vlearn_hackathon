# AI SPEC — Adaptive Glossary Learning Loop cho VLearn · Nhóm Nemo VLearn · Zone [chưa cập nhật]

Hướng: [x] A — VLearn  [ ] B — Trợ lý Học viên  [ ] C — Làn mở
Loại: [x] Tối ưu tính năng có sẵn  [ ] Tính năng mới

> **Product vision:** biến hành động tra một thuật ngữ trên slide thành một vòng học thích ứng: phát hiện thuật ngữ khó → giải thích theo ngữ cảnh và trình độ → cho người học chọn cách học → kiểm tra hiểu → cập nhật hồ sơ → tạo flashcard và lịch ôn.
>
> **Lát cắt prototype:** để đúng yêu cầu “1 user · 1 việc · 1 quyết định AI · 1 kết quả”, bản demo tập trung vào **một thuật ngữ người học bấm/bôi đen** và **một quyết định AI trung tâm: chọn gói giải thích phù hợp với ngữ cảnh + Learning Profile hiện tại**. Câu kiểm tra, cập nhật profile và flashcard là hậu xử lý trong cùng một lượt; tự quét cả trang và nhắc spaced repetition là prototype mở rộng/roadmap nếu code chưa hoàn tất.

## §1. User & Job

### Job executor + workflow

**Job executor:** học viên mới học AI hoặc có nền tảng non-tech đang đọc slide/tài liệu trên VLearn và gặp thuật ngữ vượt quá mức hiểu hiện tại.

| Chặng | Người học đang làm gì | VLearn Tutor hiện tại | Chỗ còn fail |
|---|---|---|---|
| Mở slide | Đọc nội dung bài học | Hiển thị slide/tài liệu | Người học chưa biết từ nào là “khó với mình” |
| Gặp thuật ngữ | Bôi đen một từ/cụm từ | Đã có flow bôi đen và hỏi tutor | Phải tự nhận ra chỗ không hiểu; selection có thể thiếu context |
| Nhận giải thích | Đọc nghĩa, acronym, ví dụ | Backend đã có `/api/explain`, context, `learner_level`, acronym, example, related concepts | Level chủ yếu do user chọn thủ công; chưa đánh giá độ khó của thuật ngữ so với người học |
| Đào sâu | Muốn học theo cách hợp với mình | Có chat hỏi tiếp | Chưa có lựa chọn nhanh: Tóm tắt/Ví dụ/So sánh/Chuyên sâu |
| Kiểm tra hiểu | Tự đoán mình đã hiểu | Gần như chưa có trong log | Tutor hiếm khi hỏi lại; không có đánh giá ngay |
| Ghi nhớ | Lưu thuật ngữ | Backend đã có saved terms trong session RAM | Chưa tự tạo flashcard từ kết quả học; không bền sau restart |
| Ôn tập | Muốn nhớ lại đúng lúc | Chưa có | Chưa có lịch spaced repetition |

**Core JTBD:**
**Kiểm tra và củng cố ngay mức hiểu của mình về một thuật ngữ trong lúc đọc slide để tiếp tục bài học mà không tích lũy lỗ hổng kiến thức.**

Core JTBD không chứa tên sản phẩm hoặc chữ AI; nếu bỏ VLearn/Tutor đi, công việc của người học vẫn tồn tại.

### Job stories

1. Khi mở một slide có nhiều thuật ngữ mới, tôi muốn nhận biết từ nào có thể vượt quá trình độ hiện tại, để không vô tình bỏ qua một mắt xích quan trọng.
2. Khi bôi đen “RAG”, tôi muốn được giải thích theo đúng câu đang đọc và bằng cách phù hợp với mức của mình, để hiểu nhanh mà không đổi tab.
3. Khi vừa đọc lời giải, tôi muốn làm một câu hỏi ngắn để biết mình hiểu thật hay chỉ thấy quen mắt.
4. Khi trả lời sai, tôi muốn hệ thống điều chỉnh cách giải thích và ghi nhận lỗ hổng, để lần sau không tiếp tục đưa nội dung quá khó.
5. Khi đã học một thuật ngữ, tôi muốn có flashcard và được nhắc ôn đúng lúc, để ghi nhớ lâu hơn.

### Problem statement

Người mới học AI khi đọc slide có thể tra được nghĩa của thuật ngữ nhưng vẫn không biết thuật ngữ nào khó với chính mình, lời giải có vừa trình độ hay không và mình đã hiểu thật chưa; kết quả là họ dễ bỏ qua lỗ hổng, phải tra lặp lại và quên khái niệm sau buổi học.

### Evidence chuẩn B — mining chatlog VLearn

Nguồn: `data/vlearn-pack/chatlog/chat_history_anonymized_for_hackathon.csv`, 1.261 cặp hỏi–đáp, 369 người dùng, 585 hội thoại, từ 22–29/07/2026.

**Phương pháp đếm short-span explanation, có thể kiểm lại:**

1. Chỉ lấy `role = student`.
2. Tách `đoạn được chọn` và câu hỏi phía sau dòng đầu.
3. Gắn nhãn nếu đoạn chọn tối đa 6 token và selection/câu hỏi sau khi chuyển chữ thường, bỏ dấu chứa một trong các ý định: `giải thích đoạn bôi đen`, `giải thích`, `là gì`, `nghĩa`, `dịch nghĩa`.
4. Đếm theo `turn_id`, người theo `user_id`, hội thoại theo `conversation_id`.
5. Ghép tutor response cùng `turn_id`; `citations = []` hoặc rỗng được tính là thiếu citation.

**Kết quả:**

- 281/1.261 lượt (**22,3%**) là yêu cầu giải thích đoạn ngắn.
- 132/369 người dùng (**35,8%**) từng có loại yêu cầu này.
- Các lượt nằm trong 179/585 hội thoại (**30,6%**).
- Nhóm gặp pain hỏi trung bình **2,13 lượt/người** trong cửa sổ một tuần.
- 66/281 câu trả lời (**23,5%**) không có citation.
- Toàn bộ field `follow_ups` luôn `[]`; `misconceptions` luôn `[]`.
- Chỉ 3/2.515 tutor message có `asked_check_question = True` (data dictionary); tức hành vi kiểm tra hiểu gần như vắng mặt trong hệ thống hiện tại.
- Rating quá thưa nên không dùng để kết luận mức hài lòng.

**Ví dụ nguyên văn, có mã để kiểm lại:**

| Turn | Tin nhắn học viên |
|---|---|
| `T0990` | Chọn “Context” — hỏi: `"Context" là gì` |
| `T1087` | Chọn “Tool calling” — hỏi: `tool calling là gì` |
| `T0597` | Chọn “Zero-shot, One-shot, Few-shot, CoT” — yêu cầu giải thích cho “một sinh viên SE chưa hiểu gì về AI” |
| `T0573` | Chọn và hỏi: `RNN là gì` |
| `T0750` | Chọn “RLHF” — yêu cầu giải thích đoạn bôi đen |
| `T0587` | Chọn và hỏi: `SFT là gì, RLHF là gì` |
| `T0234` | Chọn và hỏi: `LLM là gì?` |
| `T0738` | Chọn và hỏi: `mcp là gì` |
| `T0663` | Chọn “PAIR” — hỏi: `là gì` |
| `T0004` | Chọn “KB” — hỏi: `Kb ở đây là gì` |

**Giới hạn evidence:** phép đếm đo nhu cầu giải thích đoạn ngắn, không chứng minh trực tiếp rằng người học muốn spaced repetition hay tự động quét thuật ngữ. Dữ liệu về `asked_check_question`, `follow_ups` và `misconceptions` chứng minh khoảng trống hành vi của Tutor, chưa chứng minh tác động học tập. Các giả thuyết adaptive profile/flashcard/SR phải được xác nhận trong validation.

## §2. Impact & quyết định chọn

### Bảng impact

| Ứng viên tối ưu | Bao nhiêu người/lượt | Tần suất hoặc gap | Tốn gì mỗi lần | Khả thi | Chọn? |
|---|---:|---:|---|---|---|
| Adaptive Glossary Loop: giải thích đúng mức + kiểm tra hiểu + cập nhật profile | 132 người, 281 lượt short-span | 2,13 lượt/người gặp pain; check question chỉ xuất hiện 3/2.515 tutor message | Giả thuyết 2–5 phút tra/đối chiếu và nguy cơ tưởng đã hiểu | Cao cho một term; backend đã có explain/session/save | **Chọn** |
| Chỉ sửa grounding/citation | 66/281 lượt thiếu citation | 23,5% trong nhóm short-span | Người mới khó tự kiểm, có thể học sai | Cao | Giữ làm hard requirement, không phải lát cắt riêng |
| Tự phát hiện toàn bộ thuật ngữ khó trên trang | Chưa có số nhu cầu trực tiếp | 0 implementation hiện tại | Giảm bỏ sót nhưng dễ highlight quá nhiều, gây phiền | Trung bình | Prototype mở rộng |
| Tóm tắt toàn slide | 103 người, 149 lượt | 1,45 lượt/người | Giả thuyết 3–10 phút tự tổng hợp | Trung bình; khác job | Loại |
| Sinh ví dụ/bài tập độc lập | 34 người, 48 lượt | 1,41 lượt/người | Giả thuyết 5–15 phút | Trung bình; scope rộng | Loại |

Các con số “phút/lần” là giả thuyết cần bấm giờ trong validation, không phải kết quả mining.

### Vì sao chọn

Adaptive Glossary Loop tận dụng đúng flow VLearn đã tồn tại và đánh vào khoảng trống đo được: nhu cầu tra thuật ngữ lớn (281 lượt), trong khi hệ thống hầu như không kiểm tra hiểu (3/2.515 tutor message), không ghi misconception và không có follow-up có cấu trúc. So với build một tutor mới, nhóm chỉ mở rộng dữ liệu session, output schema và UI sau lời giải.

### Ứng viên đã loại/hoãn

- **Chỉ citation:** cần làm vì an toàn nhưng không giải quyết “hiểu thật hay chưa”.
- **Tự quét toàn trang:** thuộc product vision nhưng dễ tạo alert fatigue; cần validation riêng cho ngưỡng highlight.
- **Tóm tắt slide:** khác job và đòi context rộng.
- **Bài tập mở:** khó đánh giá đáp án và độ phù hợp trong thời gian hackathon.
- **Spaced repetition đầy đủ:** cần persistence, scheduler và notification; prototype chỉ tạo metadata `next_review_at`, chưa cần dịch vụ nhắc thật.

## §3. Giải pháp tương tự đã nghiên cứu

| Giải pháp | Flow | Đáng học | Đáng né | Khác biệt của VLearn |
|---|---|---|---|---|
| ChatGPT Study Mode | Hỏi mục tiêu/trình độ, giải thích từng bước, đặt câu kiểm tra | Điều chỉnh độ khó và kiểm tra hiểu | User phải rời slide hoặc tự đưa đúng context | VLearn có sẵn slide, selection, lesson context và profile |
| NotebookLM | Hỏi trên bộ nguồn, câu trả lời có citation nhảy về nguồn | Grounding rõ ràng | Cần thiết lập notebook; không tạo vòng ôn theo từng term | Citation ngay trên slide và term card |
| Quizlet/flashcard flow | Lưu khái niệm, học và kiểm tra lặp lại | Retrieval practice và trạng thái ôn | Flashcard tách khỏi ngữ cảnh ban đầu | Thẻ giữ evidence span, slide/page và mức hiểu |
| Tutor VLearn hiện tại | Bôi đen/hỏi, giải thích, citation | Không rời bài học; đã có user/context | Hỏi lại rất hiếm, follow-up/misconception trống | Thêm adaptive explanation → check → profile → review |

Nguồn chính thức tham khảo: [ChatGPT Study Mode](https://help.openai.com/en/articles/11780217-study-mode), [NotebookLM chat và citation](https://support.google.com/notebooklm/answer/16179559?hl=en).

## §4. Thiết kế

### Flow sản phẩm mục tiêu

```text
Mở slide
→ hệ thống gợi ý thuật ngữ có thể khó với profile hiện tại
→ người học bấm hoặc bôi đen thuật ngữ
→ hệ thống giải thích đúng ngữ cảnh
→ ước lượng độ khó với người học hiện tại
→ người học chọn Tóm tắt / Ví dụ / So sánh / Chuyên sâu
→ sinh 1 câu kiểm tra
→ đánh giá câu trả lời
→ cập nhật Learning Profile
→ tạo Flashcard
→ xếp lịch Spaced Repetition
```

### Lát cắt MỘT CÂU

**Một học viên mới học AI bấm vào một thuật ngữ trên slide VLearn; hệ thống quyết định gói giải thích phù hợp nhất từ ngữ cảnh và Learning Profile hiện tại; học viên nhận một thẻ học vừa trình độ kèm một câu kiểm tra để biết mình có thể tiếp tục bài học hay cần xem lại.**

- **1 user:** học viên mới học AI đang đọc slide VLearn.
- **1 việc:** hiểu và kiểm tra hiểu một thuật ngữ.
- **1 quyết định AI:** chọn gói học phù hợp (`meaning + difficulty + explanation depth + check question`) dựa trên context/profile.
- **1 kết quả:** thẻ học thích ứng có câu kiểm tra và trạng thái `đã hiểu/cần xem lại`.

### Phần VLearn cũ đã có và phần tối ưu

| Thành phần | Hiện trạng trong code | Loại |
|---|---|---|
| Bôi đen/nhập thuật ngữ và context | Schema `/api/explain`; prototype flow bôi đen | Có sẵn |
| Giải thích, acronym, ví dụ, related concepts, confidence | `prompts.py`, `schemas.py`, `llm_client.py` | Có sẵn |
| Session, level thủ công | `sessions.py`, POST/PATCH session | Có sẵn |
| Lưu/xóa/list thuật ngữ trong RAM | saved-term endpoints | Có sẵn |
| Tự phát hiện thuật ngữ khó | Chưa có | Tối ưu mở rộng |
| `difficulty_for_learner` và lý do | Chưa có | **Tối ưu lõi** |
| 4 learning modes | Chưa có | **Tối ưu lõi** |
| Sinh/check một câu hỏi | Chưa có | **Tối ưu lõi** |
| Profile cập nhật từ kết quả | Chưa có; level chỉ sửa tay | **Tối ưu lõi** |
| Flashcard có trạng thái ôn | Chưa có | Tối ưu sau lõi |
| Notification spaced repetition | Chưa có | Roadmap/mock |

### Interaction chi tiết

1. VLearn đọc `session.learning_profile` và slide hiện tại.
2. Hệ thống có thể gạch chân nhẹ tối đa 3 thuật ngữ khó; user luôn có thể bỏ qua hoặc tự bôi đen từ khác.
3. Sau click, gửi `selected_text`, 1–2 câu xung quanh, slide/page, profile và mode.
4. AI trả nghĩa theo context, expansion, độ khó cá nhân hóa (`easy/stretch/hard`), giải thích và evidence.
5. Người học chọn:
   - **Tóm tắt:** nghĩa cốt lõi trong ≤60 từ.
   - **Ví dụ:** một ví dụ gần bối cảnh công việc/học tập.
   - **So sánh:** phân biệt với tối đa hai khái niệm gần.
   - **Chuyên sâu:** cơ chế, giới hạn và khi dùng.
6. AI sinh đúng một câu multiple-choice hoặc trả lời ngắn, chỉ kiểm đúng learning objective vừa giải thích.
7. Chấm đáp án theo rubric cố định; sai/không chắc → giải thích lại một lần và đánh dấu `needs_review`.
8. Cập nhật profile bằng rule minh bạch; không để model tự nâng/hạ level tùy ý.
9. Tạo flashcard từ output đã qua check; `next_review_at` theo rule đơn giản.

### Non-goals

1. Không xây lại toàn bộ VLearn hoặc chatbot tổng quát.
2. Không tự động mở popup trên mọi thuật ngữ; chỉ gợi ý, user quyết định.
3. Không highlight quá 3 thuật ngữ/trang trong prototype.
4. Không sinh bộ quiz dài hoặc chấm bài tự luận mở.
5. Không suy luận nghề nghiệp/trình độ từ dữ liệu nhạy cảm.
6. Không đồng bộ profile đa thiết bị trong prototype.
7. Không gửi notification thật; chỉ hiển thị lịch ôn dự kiến.
8. Không dùng một câu sai để thay đổi level toàn cục.

### Mức prototype

- [ ] Sketch
- [x] Mock
- [ ] Working

**Thật:** backend explain/session/save hiện có; ít nhất một AI call thật cho adaptive package; một câu check; rule update profile; happy/low-confidence/failure/correction.

**Mock/roadmap:** tự scan toàn slide nếu chưa tích hợp; notification spaced repetition; persistence sau restart; analytics lớp học. Trạng thái Mock được chọn vì code hiện tại chưa có các endpoint adaptive/quiz/SR.

### Automation

- [ ] Augment
- [x] Conditional
- [ ] Automate

- AI tự giải thích và sinh câu kiểm tra khi context/profile đủ.
- Khi term mơ hồ, profile thiếu hoặc source không đủ, hỏi lại/chọn thêm context.
- Profile chỉ cập nhật bằng rule có ngưỡng và user có thể sửa; không tự động đổi sau một tín hiệu.
- Việc gợi ý thuật ngữ là augment: highlight nhẹ, người học quyết định có mở hay không.

**Cost-of-error:** giải thích sai hoặc nâng level quá sớm có thể khiến người mới học sai và bỏ lỗ hổng; sửa đắt vì user khó tự phát hiện. Quên một reminder rẻ hơn, nên lịch ôn có thể tự động nhưng giải thích/profile cần conditional.

### §4b. Nguyên tắc HAX/PAIR

| Nguyên tắc | Áp cụ thể |
|---|---|
| G1 — Làm rõ hệ thống làm được gì | Tooltip nói rõ: “VLearn gợi ý thuật ngữ và kiểm tra hiểu; không thay thế tài liệu/giảng viên.” |
| G2 — Làm rõ mức độ tin cậy | Card có `Đủ ngữ cảnh/Cần thêm ngữ cảnh`; độ khó là “với profile hiện tại”, không phải nhãn tuyệt đối. |
| G8 — Gạt bỏ dễ dàng | User bỏ highlight, đóng card, bỏ qua quiz và tiếp tục slide. |
| G9 — Sửa dễ dàng | Chọn “Quá dễ/Quá khó/Sai nghĩa”, đổi mode hoặc sửa level ngay trên card. |
| G10 — Thu hẹp khi nghi ngờ | Term mơ hồ → hỏi một câu/chọn thêm context; không tạo quiz từ lời giải chưa chắc. |
| G11 — Giải thích vì sao | Hiện evidence span và lý do “xếp hard vì profile chưa có prerequisite X”. |
| G15 — Feedback chi tiết | 👎 cho phép chọn sai nghĩa, quá khó, câu hỏi lệch, ví dụ không hợp. |
| G17 — Quyền kiểm soát | Profile có màn xem/sửa; user xóa flashcard và tắt gợi ý tự động. |
| PAIR — Explainability + Trust | Citation trỏ đúng slide/page; update profile kèm signal nào đã được dùng. |
| PAIR — Errors + Graceful Failure | Tách lỗi thiếu nguồn, term mơ hồ, API lỗi, chấm không chắc và notification lỗi. |

### Dữ liệu tối thiểu

```json
{
  "learning_profile": {
    "level": "coban",
    "mastered_concepts": [],
    "needs_review": [],
    "last_updated_reason": null
  },
  "adaptive_card": {
    "term": "RAG",
    "meaning_in_context": "...",
    "difficulty_for_learner": "stretch",
    "difficulty_reason": "...",
    "mode": "example",
    "evidence_span": "...",
    "check_question": {},
    "flashcard": {},
    "next_review_at": null
  }
}
```

Rule profile prototype:

- Đúng ngay + confidence user “chắc”: cộng 1 mastery signal.
- Sai hoặc “không chắc”: thêm term vào `needs_review`.
- Chỉ chuyển level sau ít nhất 3 term khác nhau cùng domain đạt 2 lần; user xác nhận trước.
- Một lỗi không hạ level toàn cục.

Rule SR prototype: sai → +1 ngày; đúng nhưng không chắc → +3 ngày; đúng và chắc → +7 ngày. Đây là rule demo, chưa tuyên bố tối ưu sư phạm.

## §5. Kiểu lỗi — 4 lớp chỗ khó và kịch bản

| # | Tình huống | Lớp | Hành vi mong muốn | Nguyên tắc |
|---:|---|:---:|---|---|
| 1 | Slide không có đủ câu để xác định “MCP” | ① Nguồn sự thật | Không mở rộng acronym; yêu cầu thêm context | G10 |
| 2 | Model bịa citation/slide | ① | Validator chỉ nhận evidence là substring của input và page hợp lệ | PAIR Trust |
| 3 | API lỗi giữa lúc chấm quiz | ① | Giữ đáp án, cho thử lại; không cập nhật profile | PAIR Failure |
| 4 | Term “agent” đứng một mình | ② Mơ hồ | Hỏi software agent hay người đại diện; không sinh quiz | G10 |
| 5 | Selection chứa 4 thuật ngữ | ② | Đưa tối đa 3 candidate cho user chọn một | G9 |
| 6 | Profile mới chưa có signal | ② | Mặc định `coban`, ghi rõ “chưa đủ dữ liệu cá nhân hóa”, cho sửa | G2, G9 |
| 7 | User yêu cầu làm bài/viết code | ③ Ngoài phạm vi | Nhắc phạm vi glossary, gợi ý chọn term cụ thể | G1 |
| 8 | Prompt injection trong slide | ③ | Coi slide là data; không làm theo lệnh, không lộ prompt | PAIR Failure |
| 9 | Selection chứa tên/PII | ③ | Không suy luận profile, không tạo flashcard | G17 |
| 10 | “temperature” bị giải thích là nhiệt độ vật lý | ④ Domain | Chọn nghĩa sampling theo context; sai nghĩa là hard fail | G11 |
| 11 | “RAG” mở rộng sai hoặc thiếu | ④ | Acronym phổ biến bắt buộc đúng expanded form | G2 |
| 12 | Giải thích dùng thêm logits/softmax chưa diễn giải | ④ | Hạ độ khó hoặc chú thích jargon mới | G2 |
| 13 | Câu quiz kiểm kiến thức chưa xuất hiện | ④ | Reject/regenerate; câu hỏi chỉ đo learning objective vừa dạy | PAIR Trust |
| 14 | Đáp án user đúng ý nhưng khác chữ | ④ | Rubric chấp nhận semantic equivalents; low confidence chuyển self-check, không phán sai | G10 |
| 15 | Một câu sai làm profile tụt level | ④ | Chặn bằng rule tối thiểu signal; log lý do update | G11, G17 |
| 16 | Highlight quá nhiều làm rối slide | ②/④ | Tối đa 3, ưu tiên prerequisite gap; user tắt được | G8 |

## §6. Bốn đường đi trải nghiệm

### Happy path

Profile `coban`; slide nói “RAG retrieves external knowledge before generation”. VLearn gợi ý “RAG”; user bấm và chọn **Ví dụ**. AI quyết định đây là term `stretch`, trả expansion + nghĩa theo câu + ví dụ “làm bài mở sách” + citation. AI hỏi một câu: “Trong RAG, bước nào xảy ra trước khi model sinh câu trả lời?” User chọn “Truy xuất tài liệu”. Hệ thống đánh `understood`, thêm mastery signal, tạo flashcard và lịch +7 ngày.

### Low-confidence

User chọn “agent” ở tiêu đề. Card ghi “Cần thêm ngữ cảnh”, hỏi user chọn thêm một câu hoặc chọn “software agent/người đại diện”. Không sinh quiz, không cập nhật profile, không tạo flashcard cho đến khi xác định được nghĩa.

### Failure/không căn cứ

Citation không khớp hoặc API lỗi. Card không hiển thị lời giải giả; giữ selection và mode, cho “Thử lại”, “Chọn thêm đoạn” hoặc “Hỏi Tutor”. Profile và lịch ôn không thay đổi.

### Correction

User bấm “Quá khó” hoặc “Sai nghĩa”. Với “Quá khó”, AI sinh lại cùng nghĩa ở mode Tóm tắt và giải thích prerequisite. Với “Sai nghĩa”, yêu cầu thêm context, giữ phiên bản cũ trong log nhưng chỉ bản user xác nhận mới thành flashcard. Feedback là signal nhưng không trực tiếp đổi level.

### Ngoài phạm vi

Yêu cầu làm bài hoặc tiết lộ system prompt được từ chối ngắn; hệ thống gợi ý quay lại chọn thuật ngữ. Instruction trong slide không có quyền điều khiển agent.

### Case đặc thù domain

Acronym phải mở rộng đúng; từ đa nghĩa phải gắn nghĩa trong đoạn; quiz không được kiểm kiến thức ngoài card; update profile phải tích lũy nhiều signal. Vi phạm một trong các điều kiện này là hard fail dù câu trả lời đọc trôi chảy.

## §7. Kiểm thử

### Chiều chất lượng

| Chiều | Pass kiểm chứng được |
|---|---|
| Nghĩa theo context | Khớp đáp án tham chiếu và không mâu thuẫn 1–2 câu nguồn |
| Grounding | Evidence là substring của context/slide và trực tiếp hỗ trợ nghĩa |
| Acronym/domain | Expanded form đúng; không nhập nhằng khái niệm gần |
| Độ khó cá nhân hóa | Cùng term/context nhưng profile có/không prerequisite tạo nhãn/lý do phù hợp theo expected rule |
| Đúng mode | Tóm tắt ≤60 từ; Ví dụ có một tình huống; So sánh có ≤2 đối tượng; Chuyên sâu nêu cơ chế + giới hạn |
| Quiz alignment | Chỉ hỏi nội dung đã có trong card; có đáp án/rubric rõ |
| Chấm đáp án | Đáp án chuẩn và semantic equivalent đều pass; sai bản chất fail |
| Profile safety | Không update khi source/grade insufficient; không đổi level chỉ từ một signal |
| Dễ hiểu | Jargon mới được diễn giải; hai người chấm độc lập thống nhất |
| Schema/UX | JSON parse được, đúng enum/độ dài; failure không render card giả |
| An toàn | 100% injection/PII/out-of-scope theo hành vi §5 |

Một case qua khi mọi chiều bắt buộc đều pass. Hai người chấm độc lập 5 output đầu; bất đồng >1 case thì sửa guideline trước khi chạy toàn bộ.

### Golden set

**Hiện trạng:** `eval/golden_set.json` đang rỗng; chưa đạt rubric. Cần tối thiểu 28 case:

| Nhóm | Số case | Gợi ý nguồn |
|---|---:|---|
| Case thường: term rõ, 4 mode | 10 | `T0990`, `T1087`, `T0573`, `T0750`, `T0234`, transcript |
| ① Nguồn sự thật | 3 | Thiếu source, citation bịa, API/schema lỗi |
| ② Mơ hồ/profile thiếu | 3 | agent, KB, selection cắt, profile mới |
| ③ Ngoài phạm vi | 3 | Injection, PII, làm bài |
| ④ Domain/adaptive | 5 | acronym, polysemy, quiz lệch, grade semantic, update quá sớm |
| Hiếm | 4 | song ngữ, OCR lỗi, term trùng nghĩa, answer không chắc |
| **Tổng** | **28** | Ít nhất 12 case phát triển từ chatlog thật |

Mỗi record cần: `id`, `source_ref`, `selected_text`, `context`, `profile_before`, `mode`, `expected_meaning`, `expected_difficulty`, `expected_quiz_objective`, `answer_variants`, `expected_profile_delta`, `risk_layer`, `hard_fail_conditions`.

### Quality bar

> **Đạt khi ≥85% case qua trọn bộ; đồng thời 100% case injection/PII an toàn, 100% acronym phổ biến đúng, 100% citation hợp lệ hoặc chủ động insufficient, ≥90% quiz aligned, và 100% profile update tuân theo rule.**

Quality bar phải giữ nguyên sau mốc chốt. Nếu nội dung này được commit sau hạn 23:59 N1, phải ghi trung thực là cập nhật muộn.

### Kết quả các lượt chạy

| Lượt | Commit/prompt | Số case | Qua | Tỷ lệ | Hard conditions | So với bar | Lỗi chính |
|---|---|---:|---:|---:|---|---|---|
| Chưa chạy adaptive flow | — | 0 | 0 | N/A | Chưa đo | Chưa thể kết luận | Endpoint adaptive/quiz/profile chưa có; golden set rỗng |

Không điền số giả. Mọi case fail phải được giữ trong log `eval/`.

## §8. Phân công & kế hoạch

### Phân công

| Thành viên | Vai trò | Trách nhiệm |
|---|---|---|
| Lê Đình Việt | Product Owner | Chốt hướng A, JTBD, evidence/impact, spec, product flow và demo |
| Nguyễn Ngọc Huân | AI Engineer | Adaptive schema/prompt, difficulty, 4 mode, quiz generation/grading, fallback |
| Vương Đức Thoại | Fullstack Developer | Slide term interaction, mode UI, quiz UI, profile/flashcard integration |
| Quách Thanh Hưng | QA & Evaluation | 28-case golden set, scorer, eval results, validation, changelog/reflection |

### Willing users và validation CP5

Repo chưa có `validation/` và chưa có tên willing user; hiện **chưa đạt** điều kiện này.

| Người thử | Vai/trình độ | Trạng thái | Người log |
|---|---|---|---|
| [Tên 1] | Học viên non-tech | Chưa xác nhận | Lê Đình Việt |
| [Tên 2] | Người mới học AI | Chưa xác nhận | Lê Đình Việt |
| [Tên 3] | Sinh viên chuyển ngành | Chưa xác nhận | Quách Thanh Hưng |
| [Tên 4] | Học viên VLearn | Chưa xác nhận | Quách Thanh Hưng |
| [Tên 5] | Học viên VLearn | Chưa xác nhận | Quách Thanh Hưng |

Ba câu hỏi:

1. “Sau thẻ giải thích và câu kiểm tra, bạn có biết mình đã hiểu đủ để đọc tiếp không? Chỗ nào cho bạn biết?”
2. “Gợi ý thuật ngữ và độ khó có đúng với bạn không? Chỉ ra một gợi ý thừa hoặc bị thiếu.”
3. “Trong Tóm tắt/Ví dụ/So sánh/Chuyên sâu, bạn đã chọn gì và vì sao?”

Observer ghi thêm: thời gian từ click đến tiếp tục đọc, có rời tab không, quiz đúng/sai, user có phản đối update profile không, có muốn lưu flashcard không, quote nguyên văn. Quách Thanh Hưng lưu đủ log từng người.

### Multi-prototype

Trục khác biệt: **cách hệ thống đưa thuật ngữ khó**.

- **P1 — tự bật popup:** chủ động tối đa nhưng gây gián đoạn và tạo cảm giác hệ thống phán xét.
- **P2 — gạch chân nhẹ tối đa 3 term, user bấm:** vẫn giúp phát hiện nhưng giữ quyền kiểm soát.

Chọn P2 theo G8/G17. Nếu validation cho thấy user bỏ sót highlight, thử icon “3 thuật ngữ nên biết” thay vì tự bật popup.

### Kế hoạch thực thi

1. Giữ nguyên endpoint explain/session/save đang có.
2. Mở rộng schema với profile, difficulty, mode, quiz và profile delta.
3. Build một case end-to-end `RAG + profile coban + mode Ví dụ + quiz + flashcard`.
4. Build low-confidence và correction trước tự scan toàn trang.
5. Tạo 28 golden case trước tuning; chạy lượt 1 và giữ mọi fail.
6. Nếu còn thời gian, thêm term detector tối đa 3 highlight và trường `next_review_at`.
7. Notification thật và persistence để roadmap.

## §9. Changelog

| Thời điểm | Đổi gì | Vì sao |
|---|---|---|
| 30/07/2026 | Spec ban đầu chọn hướng C, glossary extension/web app | Định nghĩa bài toán ban đầu |
| 31/07/2026 | Chuyển sang **Hướng A — tối ưu VLearn Tutor hiện có** | User xác nhận sản phẩm là tối ưu flow VLearn, không phải làn mở |
| 31/07/2026 | Mở rộng vision thành detect → adaptive explanation → learning mode → check → profile → flashcard → SR | Phản ánh flow sản phẩm mới |
| 31/07/2026 | Khóa lát cắt vào một thuật ngữ và một quyết định AI về gói học phù hợp | Tuân thủ format rubric, demo được trong 5 phút |
| 31/07/2026 | Phân biệt rõ phần code đã có, tối ưu lõi và roadmap | Không tuyên bố các tính năng chưa được implement |
| 31/07/2026 | Đổi golden set mục tiêu từ glossary tĩnh sang 28 case adaptive | Cần đo thêm difficulty, mode, quiz, grading và profile safety |
