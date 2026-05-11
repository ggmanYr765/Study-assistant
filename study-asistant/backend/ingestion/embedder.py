"""Gemini text-embedding-004 via REST API."""
from __future__ import annotations
import httpx
from config import settings

_EMBED_URL = "https://generativelanguage.googleapis.com/v1/models/text-embedding-004:embedContent"
_DIM = 384


def embed_texts(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    embeddings = []
    for text in texts:
        resp = httpx.post(
            _EMBED_URL,
            params={"key": settings.gemini_api_key},
            json={
                "model": "models/text-embedding-004",
                "content": {"parts": [{"text": text}]},
                "taskType": "RETRIEVAL_DOCUMENT",
                "outputDimensionality": _DIM,
            },
            timeout=30,
        )
        resp.raise_for_status()
        embeddings.append(resp.json()["embedding"]["values"])
    return embeddings


def embed_query(query: str) -> list[float]:
    resp = httpx.post(
        _EMBED_URL,
        params={"key": settings.gemini_api_key},
        json={
            "model": "models/text-embedding-004",
            "content": {"parts": [{"text": query}]},
            "taskType": "RETRIEVAL_QUERY",
            "outputDimensionality": _DIM,
        },
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["embedding"]["values"]
