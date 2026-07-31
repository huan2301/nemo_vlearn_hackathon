from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional


def log_explain_interaction(
    *,
    selected_text: str,
    surrounding_context: str,
    learner_level: str,
    explain_style: str,
    session_id: Optional[str],
    document_title: Optional[str],
    url: Optional[str],
    used_model: str,
    response_data: Dict[str, Any],
) -> None:
    """Log explain interactions to a JSONL file if possible."""
    log_dir = Path(__file__).resolve().parent.parent.parent / "eval"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / "live_interactions.jsonl"

    entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "selected_text": selected_text,
        "surrounding_context": surrounding_context,
        "learner_level": learner_level,
        "explain_style": explain_style,
        "session_id": session_id,
        "document_title": document_title,
        "url": url,
        "used_model": used_model,
        "response_data": response_data,
    }

    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
