"""Document ingestion pipeline.

Document -> text extraction -> chunking -> metadata -> embeddings -> vector
store -> retrieval. Supports .txt/.md/.pdf/.docx; page/section metadata is
preserved where the format provides it.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from ...utils.logging import get_logger

logger = get_logger(__name__)

CHUNK_SIZE = 900
CHUNK_OVERLAP = 150


@dataclass
class ExtractedText:
    text: str
    page: int | None = None
    section: str = ""


@dataclass
class Chunk:
    text: str
    page: int | None = None
    section: str = ""
    meta: dict = field(default_factory=dict)


def extract_text(path: Path) -> list[ExtractedText]:
    """Extract text from a file, returning per-page/per-section segments."""
    suffix = path.suffix.lower()
    try:
        if suffix in (".txt", ".md", ".markdown", ".csv", ".json"):
            return [ExtractedText(path.read_text(encoding="utf-8", errors="replace"))]
        if suffix == ".pdf":
            from pypdf import PdfReader

            reader = PdfReader(str(path))
            pages = []
            for i, page in enumerate(reader.pages):
                pages.append(ExtractedText(page.extract_text() or "", page=i + 1))
            return pages
        if suffix == ".docx":
            import docx

            document = docx.Document(str(path))
            sections = [p.text for p in document.paragraphs if p.text.strip()]
            return [ExtractedText("\n".join(sections))]
        raise ValueError(f"Unsupported file type: {suffix}")
    except Exception as exc:  # noqa: BLE001
        logger.warning("Text extraction failed for %s: %s", path.name, exc)
        raise


def chunk_text(
    text: str,
    page: int | None = None,
    section: str = "",
    meta: dict | None = None,
    chunk_size: int = CHUNK_SIZE,
    overlap: int = CHUNK_OVERLAP,
) -> list[Chunk]:
    """Split text into overlapping chunks on paragraph/sentence boundaries."""
    if not text or not text.strip():
        return []
    text = re.sub(r"\s+", " ", text).strip()
    chunks: list[Chunk] = []
    if len(text) <= chunk_size:
        chunks.append(Chunk(text, page, section, dict(meta or {})))
        return chunks

    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        if end < len(text):
            # Try to break at a sentence boundary near the end.
            window = text[start:end]
            for sep in (". ", "! ", "? ", "\n"):
                idx = window.rfind(sep)
                if idx > chunk_size // 2:
                    end = start + idx + 1
                    break
        chunks.append(Chunk(text[start:end].strip(), page, section, dict(meta or {})))
        if end >= len(text):
            break
        start = end - overlap
    return chunks
