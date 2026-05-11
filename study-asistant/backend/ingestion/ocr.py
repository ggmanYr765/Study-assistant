"""OCR via OpenRouter (OpenAI-compatible)."""
from __future__ import annotations
from openai import OpenAI
from config import settings

_client = OpenAI(
    api_key=settings.openrouter_api_key,
    base_url="https://openrouter.ai/api/v1",
)

OCR_PROMPT = "Extract ALL text from this image. Preserve structure: headings, bullet points, numbered lists. Mark formulas with [FORMULA: ...]. Output clean structured text only."


def ocr_image(base64_image: str) -> str:
    response = _client.chat.completions.create(
        model="meta-llama/llama-3.2-11b-vision-instruct",
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": OCR_PROMPT},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_image}"}},
            ],
        }],
        max_tokens=4096,
    )
    return response.choices[0].message.content or ""


def ocr_images(base64_images: list[str]) -> str:
    results = []
    for img in base64_images:
        try:
            results.append(ocr_image(img))
        except Exception as e:
            print(f"OCR error: {e}", flush=True)
    return "\n\n".join(r for r in results if r.strip())
