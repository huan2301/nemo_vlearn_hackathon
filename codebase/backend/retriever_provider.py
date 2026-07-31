"""
retriever_provider.py — Nạp SlideRetriever MỘT LẦN khi backend khởi động và cho
các nơi khác trong app dùng lại, mà không làm sập backend nếu chưa build index.

Đặt file này cùng thư mục với retriever.py trong codebase/backend/.
"""

import logging
import os
from pathlib import Path
from typing import Optional

from retriever import SlideRetriever

logger = logging.getLogger("vlearn_retriever_provider")
logger.setLevel(logging.INFO)


def _resolve_index_path() -> Path:
    override = os.getenv("SLIDE_INDEX_PATH")
    if override:
        return Path(override)
    # retriever_provider.py -> codebase/backend/ -> codebase/ -> <repo>/ -> data/slide_index.jsonl
    return Path(__file__).resolve().parent.parent.parent / "data" / "slide_index.jsonl"


_retriever_instance: Optional[SlideRetriever] = None
_load_attempted = False


def get_retriever() -> Optional[SlideRetriever]:
    """Trả về SlideRetriever đã nạp, hoặc None nếu chưa build index / lỗi khi nạp.
    Chỉ thử nạp 1 lần (cache); nếu lỗi thì mọi lần gọi sau trả None ngay, không
    thử đọc lại file mỗi request."""
    global _retriever_instance, _load_attempted

    if _load_attempted:
        return _retriever_instance

    _load_attempted = True
    index_path = _resolve_index_path()

    if not index_path.exists():
        logger.info(f"Slide index chưa tồn tại tại {index_path} — bỏ qua retrieval "
                    f"(chạy build_index.py để bật tính năng này).")
        return None

    try:
        _retriever_instance = SlideRetriever(index_path)
        logger.info(f"Đã nạp slide index: {len(_retriever_instance.chunks)} chunk(s) từ {index_path}")
    except Exception as e:
        logger.warning(f"Không nạp được slide index tại {index_path}: {e}")
        _retriever_instance = None

    return _retriever_instance