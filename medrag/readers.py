from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


SUPPORTED_SUFFIXES = {".pdf", ".docx", ".txt", ".md"}


@dataclass(frozen=True)
class SourceSection:
    text: str
    locator: str


def discover_documents(directory: Path) -> list[Path]:
    return sorted(
        p for p in directory.rglob("*")
        if p.is_file() and p.suffix.lower() in SUPPORTED_SUFFIXES and not p.name.startswith("~$")
    )


def read_document(path: Path) -> list[SourceSection]:
    suffix = path.suffix.lower()
    if suffix in {".txt", ".md"}:
        return [SourceSection(path.read_text(encoding="utf-8", errors="ignore"), "document")]
    if suffix == ".pdf":
        import fitz

        with fitz.open(path) as doc:
            return [SourceSection(page.get_text("text"), f"page {i + 1}") for i, page in enumerate(doc)]
    if suffix == ".docx":
        import docx

        document = docx.Document(path)
        return [SourceSection(p.text, f"paragraph {i + 1}") for i, p in enumerate(document.paragraphs) if p.text.strip()]
    raise ValueError(f"unsupported document type: {suffix}")


def chunk_sections(
    sections: Iterable[SourceSection],
    chunk_chars: int = 1800,
    overlap_chars: int = 240,
) -> list[SourceSection]:
    chunks: list[SourceSection] = []
    for section in sections:
        text = re.sub(r"[ \t]+", " ", section.text or "")
        text = re.sub(r"\n{3,}", "\n\n", text).strip()
        if not text:
            continue
        start = 0
        part = 1
        while start < len(text):
            end = min(len(text), start + chunk_chars)
            if end < len(text):
                boundary = max(text.rfind(". ", start, end), text.rfind("\n", start, end))
                if boundary > start + chunk_chars // 2:
                    end = boundary + 1
            chunks.append(SourceSection(text[start:end].strip(), f"{section.locator}, chunk {part}"))
            if end >= len(text):
                break
            start = max(start + 1, end - overlap_chars)
            part += 1
    return chunks

