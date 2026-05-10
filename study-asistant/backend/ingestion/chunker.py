"""Semantic chunker that preserves document structure."""
from __future__ import annotations
import re
from dataclasses import dataclass, field

from ingestion.parser import ParsedDocument, ParsedPage


@dataclass
class Chunk:
    content: str
    heading: str
    chunk_type: str  # text | question | formula | definition
    page_number: int
    metadata: dict = field(default_factory=dict)


HEADING_RE = re.compile(r"^(#{1,4} .+|[A-Z][A-Z\s]{4,}:?)$", re.MULTILINE)
QUESTION_RE = re.compile(
    r"(?:^|\n)(\d+[\.\)]\s.{10,}[?]|Q\d+[\.\):\s].{10,})", re.IGNORECASE
)
FORMULA_RE = re.compile(r"\[FORMULA:.+?\]", re.DOTALL)
DEFINITION_RE = re.compile(
    r"(?:Definition|Define|Def\.?):?\s+(.+)", re.IGNORECASE
)

MAX_CHUNK_CHARS = 1200
MIN_CHUNK_CHARS = 80


def _detect_type(text: str) -> str:
    if QUESTION_RE.search(text):
        return "question"
    if FORMULA_RE.search(text):
        return "formula"
    if DEFINITION_RE.search(text):
        return "definition"
    return "text"


def _split_by_headings(text: str) -> list[tuple[str, str]]:
    """Return list of (heading, body) pairs."""
    parts: list[tuple[str, str]] = []
    current_heading = ""
    current_body: list[str] = []

    for line in text.split("\n"):
        if HEADING_RE.match(line.strip()):
            if current_body:
                parts.append((current_heading, "\n".join(current_body).strip()))
                current_body = []
            current_heading = line.strip()
        else:
            current_body.append(line)

    if current_body:
        parts.append((current_heading, "\n".join(current_body).strip()))

    return parts


def _split_long(text: str, heading: str, page: int) -> list[Chunk]:
    """Split text that exceeds MAX_CHUNK_CHARS into overlapping chunks."""
    chunks: list[Chunk] = []
    paragraphs = re.split(r"\n{2,}", text)
    current: list[str] = []
    current_len = 0

    for para in paragraphs:
        if current_len + len(para) > MAX_CHUNK_CHARS and current:
            body = "\n\n".join(current)
            chunks.append(Chunk(
                content=body,
                heading=heading,
                chunk_type=_detect_type(body),
                page_number=page,
            ))
            # overlap: keep last paragraph
            current = [current[-1], para]
            current_len = len(current[-2]) + len(para)
        else:
            current.append(para)
            current_len += len(para)

    if current:
        body = "\n\n".join(current)
        if len(body) >= MIN_CHUNK_CHARS:
            chunks.append(Chunk(
                content=body,
                heading=heading,
                chunk_type=_detect_type(body),
                page_number=page,
            ))

    return chunks


def chunk_page(page: ParsedPage, text: str) -> list[Chunk]:
    chunks: list[Chunk] = []
    sections = _split_by_headings(text)

    for heading, body in sections:
        if not body or len(body) < MIN_CHUNK_CHARS:
            continue
        if len(body) > MAX_CHUNK_CHARS:
            chunks.extend(_split_long(body, heading, page.page_number))
        else:
            chunks.append(Chunk(
                content=body,
                heading=heading,
                chunk_type=_detect_type(body),
                page_number=page.page_number,
            ))

    return chunks


def chunk_document(doc: ParsedDocument, page_texts: dict[int, str]) -> list[Chunk]:
    """
    page_texts: {page_number: final_text} (may include OCR output for image pages)
    """
    all_chunks: list[Chunk] = []
    for page in doc.pages:
        text = page_texts.get(page.page_number, page.text)
        if text:
            all_chunks.extend(chunk_page(page, text))
    return all_chunks
