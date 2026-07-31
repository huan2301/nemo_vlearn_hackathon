# Benchmark & Evaluation Logs (`eval/`)

Thư mục `eval/` chứa bộ dữ liệu chuẩn (Golden Set) và lịch sử các lượt chạy kiểm thử tự động cho **VLearn AI Tutor & Glossary Prototype**.

## 📊 Kết Quả Lượt Chạy Đánh Giá Mới Nhất (Lượt 1)

- **Thời gian chạy:** `2026-07-31T10:41:53.868082`
- **AI Model chính:** `llama-3.3-70b-versatile`
- **Tổng số test cases:** `24`
- **Số case ĐẠT (Pass):** `18/24`
- **Tỷ lệ Đạt (Pass Rate):** `75.0%` (Chỉ tiêu Quality Bar: `≥85.0%`)
- **Trạng thái:** `❌ CHƯA ĐẠT QUALITY BAR`

---

## 📈 Lịch Sử Các Lượt Chạy (Benchmark History)

| Lượt | Thời điểm | Model + Prompt | Số case | Case qua | Tỷ lệ | So với Quality Bar (≥85%) | Ghi chú lỗi chính |
|---|---|---|---:|---:|---:|---|---|
| Lượt 1 | 31/07/2026 10:41 | `groq/llama-3.3-70b-versatile` | 24 | 18 | **75.0%** | ❌ Chưa đạt |  |

> Bảng trên được sinh tự động từ `eval_history.json` — mỗi lần chạy `run_eval.py` sẽ **thêm một dòng mới**,
> không ghi đè lên các lượt trước. Chi tiết đầy đủ của từng lượt được lưu riêng tại
> `eval_results_run<NN>_<timestamp>.json`.

---

## 🛡️ Hard Fail Conditions Verification (lượt 1)

1. **Safety & Prompt Injection (100% Pass):** `0` vi phạm.
2. **Acronym Expansion Accuracy (100% Pass):** `3` vi phạm.
3. **Grounding & Evidence Span:** 100% case có trích dẫn hoặc chủ động báo thiếu ngữ cảnh.

---

## 📁 Cấu Trúc File Trong `eval/`

- `golden_set.json`: 24 kịch bản kiểm thử bao phủ 4 lớp chỗ khó (§5) và case đặc thù.
- `eval_history.json`: Tóm tắt **tất cả** các lượt chạy đã thực hiện (tích lũy qua thời gian).
- `eval_results.json`: Kết quả chi tiết của lượt chạy **gần nhất**.
- `eval_results_run<NN>_<timestamp>.json`: Kết quả chi tiết đầy đủ của **từng lượt** riêng biệt (archive).
- `run_eval.py`: Script tự động chạy benchmark đánh giá hệ thống.
- `README.md`: Bảng tổng hợp kết quả đánh giá các lượt chạy (tự sinh lại mỗi lần chạy).
