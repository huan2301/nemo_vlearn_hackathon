from __future__ import annotations

import json
import math
import re
import unicodedata
from collections import Counter
from dataclasses import dataclass
from pathlib import Path


TOKEN_PATTERN = re.compile(r"[a-z0-9]+", re.IGNORECASE)
RAW_VIETNAMESE_STOPWORDS = {
    "ai",
    "bài",
    "bạn",
    "các",
    "cho",
    "có",
    "của",
    "được",
    "gì",
    "giải",
    "hãy",
    "không",
    "là",
    "một",
    "nào",
    "như",
    "những",
    "theo",
    "thế",
    "trong",
    "tôi",
    "và",
    "về",
}


def normalize(text: str) -> str:
    decomposed = unicodedata.normalize("NFD", text.lower())
    return "".join(char for char in decomposed if unicodedata.category(char) != "Mn")


VIETNAMESE_STOPWORDS = {normalize(word) for word in RAW_VIETNAMESE_STOPWORDS}


def tokenize(text: str) -> list[str]:
    return [
        token
        for token in TOKEN_PATTERN.findall(normalize(text))
        if len(token) > 1 and token not in VIETNAMESE_STOPWORDS
    ]


@dataclass(frozen=True)
class SearchResult:
    chunk: dict[str, object]
    score: float

    def to_dict(self) -> dict[str, object]:
        return {
            "chunk_id": self.chunk["chunk_id"],
            "document_id": self.chunk["document_id"],
            "document_title": self.chunk["document_title"],
            "page": self.chunk["page"],
            "page_title": self.chunk["page_title"],
            "citation": self.chunk["citation"],
            "content": self.chunk["content"],
            "score": round(self.score, 4),
        }


class SlideRetriever:
    """Small BM25-like index suitable for the 58-page hackathon corpus."""

    def __init__(self, jsonl_path: Path):
        self.jsonl_path = jsonl_path
        self.chunks = [
            json.loads(line)
            for line in jsonl_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        if not self.chunks:
            raise ValueError("Slide index is empty")

        self.term_frequencies: list[Counter[str]] = []
        document_frequency: Counter[str] = Counter()
        for chunk in self.chunks:
            frequencies = Counter(tokenize(str(chunk["content"])))
            self.term_frequencies.append(frequencies)
            document_frequency.update(frequencies.keys())

        corpus_size = len(self.chunks)
        self.idf = {
            term: math.log(1 + (corpus_size - count + 0.5) / (count + 0.5))
            for term, count in document_frequency.items()
        }

    def search(
        self,
        query: str,
        limit: int = 4,
        document_id: str | None = None,
    ) -> list[SearchResult]:
        query_tokens = tokenize(query)
        if not query_tokens:
            return []

        results: list[SearchResult] = []
        for chunk, frequencies in zip(self.chunks, self.term_frequencies):
            if document_id and chunk["document_id"] != document_id:
                continue

            score = 0.0
            for token in query_tokens:
                term_frequency = frequencies.get(token, 0)
                if term_frequency:
                    score += self.idf.get(token, 0.0) * (
                        1.0 + math.log(term_frequency)
                    )

            if score > 0:
                results.append(SearchResult(chunk=chunk, score=score))

        return sorted(results, key=lambda item: item.score, reverse=True)[:limit]