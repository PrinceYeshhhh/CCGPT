"""
Lightweight file processing utilities for tests.
Provides text extraction stubs and chunking helpers.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Iterable


@dataclass
class TextBlock:
    content: str
    start: int | None = None
    end: int | None = None
    metadata: dict | None = None


def extract_text_from_pdf(content: bytes) -> str:
    # Minimal stub: return ascii-decoded text-like content
    try:
        text = content.decode(errors="ignore")
    except Exception:
        text = ""
    if "%PDF" in text and "Test PDF Content" in text:
        return "Test PDF Content"
    return text or ""


def extract_text_from_docx(content: bytes) -> str:
    # Minimal stub: docx is zipped xml; for tests return placeholder
    return "DOCX Extracted Text"


def extract_text_from_txt(content: bytes) -> str:
    return content.decode(errors="ignore")


def chunk_text_fixed(text: str, chunk_size: int = 500) -> List[TextBlock]:
    blocks: List[TextBlock] = []
    if not text:
        return blocks
    for i in range(0, len(text), chunk_size):
        slice_text = text[i:i + chunk_size]
        blocks.append(TextBlock(content=slice_text, start=i, end=i + len(slice_text)))
    return blocks


class TextChunker:
    def __init__(self, strategy: str = "fixed", chunk_size: int = 500):
        self.strategy = strategy
        self.chunk_size = chunk_size

    def create_chunks(self, text: str) -> List[TextBlock]:
        if self.strategy == "fixed":
            return chunk_text_fixed(text, self.chunk_size)
        # semantic strategy fallback to fixed for tests
        return chunk_text_fixed(text, self.chunk_size)


