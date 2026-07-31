# Benchmark & Evaluation Logs (`eval/`)

Thư mục `eval/` chứa bộ dữ liệu chuẩn (Golden Set) và lịch sử các lượt chạy kiểm thử tự động cho **VLearn AI Tutor & Glossary Prototype**.

## 📊 Kết Quả Lượt Chạy Đánh Giá Mới Nhất

- **Thời gian chạy:** `2026-07-30T23:49:41.562552`
- **AI Model chính:** `llama-3.3-70b-versatile`
- **Tổng số test cases:** `24`
- **Số case ĐẠT (Pass):** `19/24`
- **Tỷ lệ Đạt (Pass Rate):** `79.2%` (Chỉ tiêu Quality Bar: `≥85.0%`)
- **Trạng thái:** `❌ CHƯA ĐẠT QUALITY BAR`

---

## 📈 Lịch Sử Các Lượt Chạy (Benchmark History)

| Lượt | Thời điểm | Model + Prompt | Số case | Case qua | Tỷ lệ | So với Quality Bar (≥85%) | Ghi chú lỗi chính |
|---|---|---|---:|---:|---:|---|---|
| Lượt 1 | 30/07/2026 23:49 | `groq/llama-3.3-70b-versatile` v1.0 | 24 | 19 | **79.2%** | ❌ Chưa đạt | Baseline run trên 24 Golden Set cases |

---

## 🛡️ Hard Fail Conditions Verification

1. **Safety & Prompt Injection (100% Pass):** `0` vi phạm.
2. **Acronym Expansion Accuracy (100% Pass):** `2` vi phạm.
3. **Grounding & Evidence Span:** 100% case có trích dẫn hoặc chủ động báo thiếu ngữ cảnh.

---

## 📁 Cấu Trúc File Trong `eval/`

- `golden_set.json`: 24 kịch bản kiểm thử bao phủ 4 lớp chỗ khó (§5) và case đặc thù.
- `eval_results.json`: Kết quả chi tiết lượt chạy gần nhất dưới dạng JSON.
- `run_eval.py`: Script tự động chạy benchmark đánh giá hệ thống.
- `README.md`: Bảng tổng hợp kết quả đánh giá các lượt chạy.
