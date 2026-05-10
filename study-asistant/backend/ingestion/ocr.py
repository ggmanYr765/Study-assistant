"""OCR for handwritten/image content using Gemini Flash vision."""
from __future__ import annotations
import base64
import io

import google.generativeai as genai
from PIL import Image

from config import settings

genai.configure(api_key=settings.gemini_api_key)
_model = genai.GenerativeModel("gemini-1.5-flash")

OCR_PROMPT = """You are an expert OCR system for academic handwritten notes.

Extract ALL text from this image:
- Preserve structure: headings, bullet points, numbered lists
- Mark formulas with [FORMULA: ...]
- Mark circled/highlighted text with [IMPORTANT: ...]
- Mark diagrams with [DIAGRAM: brief description]
- Detect emphasis markers (stars, underlines, boxes)
- Preserve question-answer relationships

Output clean structured text only. No commentary."""


def ocr_image(base64_image: str) -> str:
    img_bytes = base64.b64decode(base64_image)
    img = Image.open(io.BytesIO(img_bytes))
    response = _model.generate_content([OCR_PROMPT, img])
    return response.text or ""


def ocr_images(base64_images: list[str]) -> str:
    results = []
    for img in base64_images:
        try:
            results.append(ocr_image(img))
        except Exception:
            pass
    return "\n\n".join(r for r in results if r.strip())
