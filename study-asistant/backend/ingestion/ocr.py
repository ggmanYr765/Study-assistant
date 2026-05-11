"""OCR via Gemini 2.0 Flash REST API."""
from __future__ import annotations
import httpx
from config import settings

_GEN_URL = "https://generativelanguage.googleapis.com/v1/models/gemini-2.0-flash:generateContent"

OCR_PROMPT = "Extract ALL text from this image. Preserve structure: headings, bullet points, numbered lists. Mark formulas with [FORMULA: ...]. Output clean structured text only."


def ocr_image(base64_image: str) -> str:
    resp = httpx.post(
        _GEN_URL,
        params={"key": settings.gemini_api_key},
        json={
            "contents": [{
                "parts": [
                    {"text": OCR_PROMPT},
                    {"inline_data": {"mime_type": "image/png", "data": base64_image}},
                ]
            }]
        },
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json()["candidates"][0]["content"]["parts"][0]["text"]


def ocr_images(base64_images: list[str]) -> str:
    results = []
    for img in base64_images:
        try:
            results.append(ocr_image(img))
        except Exception as e:
            print(f"OCR error: {e}", flush=True)
    return "\n\n".join(r for r in results if r.strip())
