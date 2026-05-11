"""Gemini text-embedding-004 — no heavy local models needed."""
from __future__ import annotations

import google.generativeai as genai
from config import settings

genai.configure(api_key=settings.gemini_api_key)

_EMBED_MODEL = "models/text-embedding-004"
_DIM = 384


def embed_texts(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    embeddings = []
    for text in texts:
        result = genai.embed_content(
            model=_EMBED_MODEL,
            content=text,
            task_type="retrieval_document",
            output_dimensionality=_DIM,
        )
        embeddings.append(result["embedding"])
    return embeddings


def embed_query(query: str) -> list[float]:
    result = genai.embed_content(
        model=_EMBED_MODEL,
        content=query,
        task_type="retrieval_query",
        output_dimensionality=_DIM,
    )
    return result["embedding"]
