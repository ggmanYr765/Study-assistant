"""Base DeepSeek agent using the OpenAI-compatible async API."""
from __future__ import annotations

from openai import AsyncOpenAI

from config import settings

client = AsyncOpenAI(
    api_key=settings.deepseek_api_key,
    base_url="https://api.deepseek.com",
)


async def run_agent(
    system: str,
    messages: list[dict],
    model: str | None = None,
    max_tokens: int = 4096,
) -> str:
    used_model = model or settings.smart_model
    response = await client.chat.completions.create(
        model=used_model,
        max_tokens=max_tokens,
        messages=[{"role": "system", "content": system}, *messages],
    )
    return response.choices[0].message.content or ""


async def stream_agent(
    system: str,
    messages: list[dict],
    model: str | None = None,
    max_tokens: int = 4096,
):
    """Async generator yielding text deltas from a streaming DeepSeek inference."""
    used_model = model or settings.smart_model
    stream = await client.chat.completions.create(
        model=used_model,
        max_tokens=max_tokens,
        messages=[{"role": "system", "content": system}, *messages],
        stream=True,
    )
    async for chunk in stream:
        delta = chunk.choices[0].delta.content
        if delta:
            yield delta
