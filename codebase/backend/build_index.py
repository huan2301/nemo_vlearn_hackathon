"""
build_index.py — Dựng file JSONL index cho SlideRetriever từ dữ liệu thật trong data/.

Chạy: python build_index.py --input ../../data --output ../../data/slide_index.jsonl

MỖI DÒNG trong file output là 1 chunk, đúng schema mà retriever.py cần:
    {
      "chunk_id": "vd_slide2_p07_c00",
      "document_id": "vd_slide2",          # dùng để lọc theo tài liệu (ExplainRequest.document_title)
      "document_title": "Buổi 2 - RLHF...",
      "page": 7,
      "page_title": "RLHF là gì?",          # optional, để trống nếu không tách được
      "citation": "Buổi 2, trang 7",        # chuỗi hiển thị cho người học biết nguồn
      "content": "toàn bộ text của chunk này..."
    }

NGUỒN DỮ LIỆU HỖ TRỢ:
  - "*.pdf"        : file slide THẬT trong data/vlearn-pack/slides/ — mỗi trang PDF
                      tách text bằng pypdf, 1 chunk = đúng 1 trang PDF (giữ số trang thật).
  - "*.txt"/"*.md" : file transcript/text đã export — tách trang theo 1 trong 3 chế độ
                      dưới đây (SPLIT_MODE).

CÁCH TÁCH TRANG (page splitting) CHO .txt/.md — chỉnh 1 trong 3 chế độ dưới đây cho khớp
định dạng file thật của bạn trong data/:

  1. "formfeed"  : mỗi trang cách nhau bằng ký tự \f (một số công cụ export PDF->txt dùng cái này)
  2. "marker"    : mỗi trang bắt đầu bằng một dòng khớp PAGE_MARKER_REGEX, ví dụ "=== Slide 7 ==="
  3. "paragraph" : không có marker trang -> cứ N từ thì cắt thành 1 chunk (mặc định N=150)

Mặc định dùng "paragraph" vì an toàn với mọi định dạng text thô. Nếu data của bạn có
marker trang rõ ràng, đổi SPLIT_MODE = "marker" và sửa PAGE_MARKER_REGEX cho khớp.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

# ---- Chỉnh 2 biến này cho khớp định dạng file .txt/.md thật trong data/ của bạn ----
SPLIT_MODE = "paragraph"  # "formfeed" | "marker" | "paragraph"
PAGE_MARKER_REGEX = re.compile(r"^===\s*(?:Slide|Trang|Page)\s*(\d+)\s*(.*)===\s*$", re.IGNORECASE)
WORDS_PER_CHUNK = 150  # chỉ dùng khi SPLIT_MODE == "paragraph"

TEXT_EXTENSIONS = {".txt", ".md"}
PDF_EXTENSIONS = {".pdf"}
SUPPORTED_EXTENSIONS = TEXT_EXTENSIONS | PDF_EXTENSIONS


def split_formfeed(raw_text: str) -> list[tuple[int, str, str]]:
    """Trả về list (page_number, page_title, page_text)."""
    pages = raw_text.split("\f")
    return [(i + 1, "", page.strip()) for i, page in enumerate(pages) if page.strip()]


def split_marker(raw_text: str) -> list[tuple[int, str, str]]:
    lines = raw_text.splitlines()
    pages: list[tuple[int, str, str]] = []
    current_page_num = 0
    current_title = ""
    current_lines: list[str] = []

    def flush():
        text = "\n".join(current_lines).strip()
        if text:
            pages.append((current_page_num, current_title, text))

    for line in lines:
        m = PAGE_MARKER_REGEX.match(line.strip())
        if m:
            flush()
            current_page_num = int(m.group(1))
            current_title = (m.group(2) or "").strip()
            current_lines = []
        else:
            current_lines.append(line)
    flush()
    return pages


def split_paragraph(raw_text: str, words_per_chunk: int = WORDS_PER_CHUNK) -> list[tuple[int, str, str]]:
    words = raw_text.split()
    chunks = []
    for i in range(0, len(words), words_per_chunk):
        chunk_words = words[i : i + words_per_chunk]
        page_num = i // words_per_chunk + 1
        chunks.append((page_num, "", " ".join(chunk_words)))
    return chunks


def split_into_pages(raw_text: str) -> list[tuple[int, str, str]]:
    if SPLIT_MODE == "formfeed":
        return split_formfeed(raw_text)
    if SPLIT_MODE == "marker":
        return split_marker(raw_text)
    return split_paragraph(raw_text)


def extract_pdf_pages(file_path: Path) -> list[tuple[int, str, str]]:
    """Tách 1 file PDF thật (VD: data/vlearn-pack/slides/d1-slide-hackathon.pdf) thành
    list (page_number, page_title, page_text) — MỖI CHUNK = ĐÚNG 1 TRANG PDF THẬT,
    giữ nguyên số trang gốc để citation ("trang N") luôn chính xác.

    Cần thư viện pypdf: pip install pypdf (đã có trong requirements.txt).
    """
    try:
        from pypdf import PdfReader
    except ImportError as e:
        raise RuntimeError(
            "Thiếu thư viện pypdf để đọc file PDF slide. Chạy: pip install pypdf"
        ) from e

    reader = PdfReader(str(file_path))
    pages: list[tuple[int, str, str]] = []
    for i, page in enumerate(reader.pages):
        text = (page.extract_text() or "").strip()
        if not text:
            continue
        pages.append((i + 1, "", text))
    return pages


def build_index(input_dir: Path, output_path: Path) -> int:
    total_chunks = 0
    with open(output_path, "w", encoding="utf-8") as out_f:
        for file_path in sorted(input_dir.rglob("*")):
            suffix = file_path.suffix.lower()
            if suffix not in SUPPORTED_EXTENSIONS:
                continue

            document_id = file_path.stem
            document_title = file_path.stem.replace("_", " ").replace("-", " ")

            if suffix in PDF_EXTENSIONS:
                try:
                    pages = extract_pdf_pages(file_path)
                except Exception as e:
                    print(f"[ERROR] Không đọc được PDF {file_path.name}: {e}")
                    continue
            else:
                raw_text = file_path.read_text(encoding="utf-8", errors="ignore")
                pages = split_into_pages(raw_text)

            for page_idx, (page_num, page_title, page_text) in enumerate(pages):
                if not page_text.strip():
                    continue
                chunk_id = f"{document_id}_p{page_num:03d}_c{page_idx:02d}"
                citation = f"{document_title}, trang {page_num}"
                record = {
                    "chunk_id": chunk_id,
                    "document_id": document_id,
                    "document_title": document_title,
                    "page": page_num,
                    "page_title": page_title,
                    "citation": citation,
                    "content": page_text.strip(),
                }
                out_f.write(json.dumps(record, ensure_ascii=False) + "\n")
                total_chunks += 1

            print(f"[OK] {file_path.name}: {len(pages)} chunk(s)")

    return total_chunks


def main():
    parser = argparse.ArgumentParser(description="Build JSONL slide/transcript index for SlideRetriever")
    parser.add_argument("--input", required=True, help="Thư mục chứa file .pdf/.txt/.md thật (VD: ../../data)")
    parser.add_argument("--output", required=True, help="Đường dẫn file JSONL output (VD: ../../data/slide_index.jsonl)")
    args = parser.parse_args()

    input_dir = Path(args.input)
    output_path = Path(args.output)

    if not input_dir.exists():
        print(f"[ERROR] Không tìm thấy thư mục input: {input_dir}")
        return

    output_path.parent.mkdir(parents=True, exist_ok=True)
    total = build_index(input_dir, output_path)

    if total == 0:
        print(f"[WARN] Không tạo được chunk nào. Kiểm tra lại SPLIT_MODE/PAGE_MARKER_REGEX "
              f"cho khớp định dạng thật của file trong {input_dir}, và đảm bảo pypdf đã cài "
              f"nếu thư mục có file .pdf.")
    else:
        print(f"[DONE] Tổng {total} chunk -> {output_path}")


if __name__ == "__main__":
    main()
