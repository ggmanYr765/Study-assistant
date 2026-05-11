"""Embeddings via HuggingFace Inference API — no local model needed."""
from __future__ import annotations
import numpy as np
import httpx

_HF_URL = "https://api-inference.huggingface.co/pipeline/feature-extraction/sentence-transformers/all-MiniLM-L6-v2"


def _embed(texts: list[str]) -> list[list[float]]:
    resp = httpx.post(
        _HF_URL,
        json={"inputs": texts, "options": {"wait_for_model": True}},
        timeout=120,
    )
    resp.raise_for_status()
    result = resp.json()
    embeddings = []
    for item in result:
        if isinstance(item[0], list):
            embeddings.append(np.mean(item, axis=0).tolist())
        else:
            embeddings.append(item)
    return embeddings


def embed_texts(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    return _embed(texts)


def embed_query(query: str) -> list[float]:
    return _embed([query])[0]
