"""Extract structured knowledge from raw document text."""
from __future__ import annotations
import json

from agents.base import run_agent
from config import settings

EXTRACT_SYSTEM = """You are an academic content analyzer for exam preparation.

Given raw text from study materials, extract:
1. Key topics and subtopics
2. Important definitions
3. Formulas and derivations
4. Questions (if this is a previous year paper)
5. High-emphasis content (starred, underlined, circled, marked important)

Return JSON only. No commentary."""

EXTRACT_PROMPT = """Analyze this content and return JSON:

{
  "topics": ["topic1", "topic2"],
  "definitions": [{"term": "...", "definition": "..."}],
  "formulas": ["formula1"],
  "questions": ["question1"],  // only if PYQ
  "important_markers": ["content marked as important"],
  "is_pyq": false,
  "year": null  // year if PYQ
}

Content:
"""


def extract_knowledge(text: str, doc_type: str) -> dict:
    prompt = EXTRACT_PROMPT + text[:6000]
    response = run_agent(
        EXTRACT_SYSTEM,
        [{"role": "user", "content": prompt}],
        model=settings.fast_model,
        max_tokens=2048,
    )
    try:
        # strip markdown fences if present
        clean = response.strip()
        if clean.startswith("```"):
            clean = clean.split("```")[1]
            if clean.startswith("json"):
                clean = clean[4:]
        return json.loads(clean)
    except Exception:
        return {
            "topics": [],
            "definitions": [],
            "formulas": [],
            "questions": [],
            "important_markers": [],
            "is_pyq": doc_type == "pyq",
            "year": None,
        }
