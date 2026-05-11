"""PDF/image file parser using pymupdf."""
from __future__ import annotations
import base64
from dataclasses import dataclass, field
from pathlib import Path

import fitz  # pymupdf


@dataclass
class ParsedPage:
    page_number: int
    text: str
    images: list[str] = field(default_factory=list)  # base64 encoded PNGs
    has_handwriting: bool = False


@dataclass
class ParsedDocument:
    filename: str
    pages: list[ParsedPage]
    page_count: int


def parse_pdf(filepath: str | Path) -> ParsedDocument:
    filepath = Path(filepath)
    doc = fitz.open(str(filepath))
    pages: list[ParsedPage] = []

    for page_num, page in enumerate(doc, start=1):
        text = page.get_text("text").strip()
        images: list[str] = []

        for img_ref in page.get_images(full=True):
            xref = img_ref[0]
            base_img = doc.extract_image(xref)
            img_bytes = base_img["image"]
            images.append(base64.b64encode(img_bytes).decode())

        # render page as image when text extraction returns nothing
        if not text and not images:
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
            images.append(base64.b64encode(pix.tobytes("png")).decode())

        # heuristic: low text density with images suggests handwriting
        has_handwriting = len(images) > 0 and len(text) < 200

        pages.append(ParsedPage(
            page_number=page_num,
            text=text,
            images=images,
            has_handwriting=has_handwriting,
        ))

    doc.close()
    return ParsedDocument(
        filename=filepath.name,
        pages=pages,
        page_count=len(pages),
    )


def parse_image(filepath: str | Path) -> ParsedDocument:
    """Wrap a single image as a one-page document."""
    filepath = Path(filepath)
    with open(filepath, "rb") as f:
        img_bytes = f.read()
    b64 = base64.b64encode(img_bytes).decode()
    page = ParsedPage(page_number=1, text="", images=[b64], has_handwriting=True)
    return ParsedDocument(filename=filepath.name, pages=[page], page_count=1)


IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp"}


def parse_file(filepath: str | Path) -> ParsedDocument:
    filepath = Path(filepath)
    if filepath.suffix.lower() in IMAGE_EXTS:
        return parse_image(filepath)
    return parse_pdf(filepath)
