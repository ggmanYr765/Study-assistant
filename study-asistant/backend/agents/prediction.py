"""Predict probable exam questions from session content."""
from __future__ import annotations
import json

from agents.base import run_agent
from config import settings

PREDICT_SYSTEM = """You are an expert exam question predictor with 15 years of experience analyzing university exam patterns.

You analyze:
- Previous year papers (PYQs) for frequency and patterns
- Professor notes for emphasis
- Syllabus coverage
- Topic repetition across years
- Question type distribution (long/short/derivation/numerical)

You NEVER fabricate. You only predict based on patterns in the provided material.
Return valid JSON only."""

PREDICT_PROMPT = """Based on this session content, predict the most probable exam questions.

Session content summary:
{context}

Return JSON array of predicted questions:
[
  {{
    "question": "full question text",
    "question_type": "long|short|derivation|numerical",
    "confidence": 0.0-1.0,
    "frequency": number_of_times_seen_in_PYQs,
    "estimated_marks": 2|5|10|15,
    "answer_outline": "bullet points of key answer points",
    "topics": ["topic1", "topic2"],
    "source_hint": "seen in 2022, 2023 papers / emphasized in professor notes"
  }}
]

Generate 15-20 questions. Order by confidence descending."""


async def predict_questions(context: str) -> list[dict]:
    response = await run_agent(
        PREDICT_SYSTEM,
        [{"role": "user", "content": PREDICT_PROMPT.format(context=context[:8000])}],
        max_tokens=4096,
    )
    try:
        clean = response.strip()
        # strip markdown fences
        if "```" in clean:
            parts = clean.split("```")
            for p in parts:
                p = p.strip()
                if p.startswith("json"):
                    p = p[4:]
                p = p.strip()
                if p.startswith("["):
                    clean = p
                    break
        # find first JSON array
        start = clean.find("[")
        end = clean.rfind("]")
        if start != -1 and end != -1:
            clean = clean[start:end+1]
        return json.loads(clean)
    except Exception:
        return []
