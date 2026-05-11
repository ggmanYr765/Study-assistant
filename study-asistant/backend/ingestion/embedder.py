"""Embeddings via OpenRouter."""
from __future__ import annotations
from openai import OpenAI
from config import settings

_client = OpenAI(
    api_key=settings.openrouter_api_key,
    base_url="https://openrouter.ai/api/v1",
)


def embed_texts(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    resp = _client.embeddings.create(
        model="openai/text-embedding-3-small",
        input=texts,
        dimensions=384,
    )
    return [item.embedding for item in resp.data]


def embed_query(query: str) -> list[float]:
    resp = _client.embeddings.create(
        model="openai/text-embedding-3-small",
        input=[query],
        dimensions=384,
    )
    return resp.data[0].embedding
