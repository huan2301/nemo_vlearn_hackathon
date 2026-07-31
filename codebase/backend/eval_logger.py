"""
eval_logger.py — Ghi log các lượt "bôi đen -> giải thích" THẬT từ demo vào eval/.

Mục đích: mỗi lần người học bôi đen 1 thuật ngữ trên frontend/extension và gọi
/api/explain, ta lưu lại request + response dưới dạng JSONL (append-only) vào
eval/live_interactions.jsonl. Đây là nguồn dữ liệu "chatlog thật" để sau này
đội ngũ xem lại và chọn lọc thành case cho golden_set.json (guide §1.3 và §2.6:
"≥10 case lấy hoặc phát triển từ chatlog thật").

Thiết kế:
- Append-only JSONL: mỗi dòng 1 JSON object độc lập -> không lo file lớn bị vỡ,
  không cần load toàn bộ file để ghi thêm 1 dòng.
- Không bao giờ raise exception ra ngoài: nếu ghi log lỗi (disk full, quyền
  file, path sai...), chỉ log cảnh báo ra console, KHÔNG làm hỏng response
  chính trả về cho người dùng.
- Thread-safe bằng Lock đơn giản (đủ dùng cho uvicorn single-worker dev server;
  nếu chạy nhiều worker/process, cân nhắc chuyển sang DB hoặc file theo worker-id).
"""

import json
import os
import logging
from datetime import datetime
from pathlib import Path
from threading import Lock
from typing import Any, Dict, Optional

logger = logging.getLogger("vlearn_eval_logger")
logger.setLevel(logging.INFO)

_WRITE_LOCK = Lock()

# File log chính: mỗi dòng là 1 lượt giải thích thật
LOG_FILENAME = "live_interactions.jsonl"


def _resolve_eval_dir() -> Path:
    """Xác định đường dẫn thư mục eval/ ở gốc repo.

    Ưu tiên biến môi trường EVAL_LOG_DIR (tiện cho việc override khi deploy).
    Mặc định: app.py nằm ở <repo>/codebase/backend/app.py -> eval/ ở
    <repo>/eval/, tức đi lên 2 cấp từ file này rồi vào "eval".
    """
    override = os.getenv("EVAL_LOG_DIR")
    if override:
        return Path(override)
    # eval_logger.py -> codebase/backend/ -> codebase/ -> <repo>/ -> eval/
    return Path(__file__).resolve().parent.parent.parent / "eval"


def _next_sequence_number(log_path: Path) -> int:
    """Đếm số dòng hiện có để đánh số thứ tự log_id liên tục (chỉ để dễ đọc,
    không dùng làm khóa duy nhất — không quan trọng nếu đếm không tuyệt đối
    chính xác khi có ghi đồng thời)."""
    if not log_path.exists():
        return 1
    try:
        with open(log_path, "r", encoding="utf-8") as f:
            count = sum(1 for _ in f)
        return count + 1
    except OSError:
        return 1


def log_explain_interaction(
    *,
    selected_text: str,
    surrounding_context: str = "",
    learner_level: str = "coban",
    explain_style: str = "tomtat",
    session_id: Optional[str] = None,
    document_title: Optional[str] = None,
    url: Optional[str] = None,
    used_model: str = "",
    response_data: Optional[Dict[str, Any]] = None,
) -> None:
    """Ghi 1 dòng log cho 1 lượt bôi đen -> giải thích thật từ demo.

    Không raise exception: mọi lỗi được nuốt và log cảnh báo, để không ảnh
    hưởng tới response chính của API.
    """
    try:
        eval_dir = _resolve_eval_dir()
        eval_dir.mkdir(parents=True, exist_ok=True)
        log_path = eval_dir / LOG_FILENAME

        response_data = response_data or {}

        entry = {
            "log_id": None,  # gán bên dưới, trong lock, để số thứ tự nhất quán
            "logged_at": datetime.now().isoformat(),
            "session_id": session_id,
            "document_title": document_title,
            "url": url,
            "request": {
                "selected_text": selected_text,
                "surrounding_context": surrounding_context,
                "learner_level": learner_level,
                "explain_style": explain_style,
            },
            "response": {
                "term": response_data.get("term"),
                "expanded_form": response_data.get("expanded_form"),
                "meaning_in_context": response_data.get("meaning_in_context"),
                "plain_explanation": response_data.get("plain_explanation"),
                "styled_explanation": response_data.get("styled_explanation"),
                "is_difficult": response_data.get("is_difficult"),
                "difficulty_reason": response_data.get("difficulty_reason"),
                "example": response_data.get("example"),
                "confidence": response_data.get("confidence"),
                "evidence_span": response_data.get("evidence_span"),
                "clarifying_question": response_data.get("clarifying_question"),
            },
            "used_model": used_model,
        }

        with _WRITE_LOCK:
            entry["log_id"] = _next_sequence_number(log_path)
            line = json.dumps(entry, ensure_ascii=False)
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(line + "\n")

    except Exception as e:
        logger.warning(f"Không ghi được live interaction log: {e}")