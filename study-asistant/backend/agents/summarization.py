"""Compression and revision sheet generation agent."""
from __future__ import annotations
import json

from agents.base import run_agent

COMPRESS_SYSTEM = """You are a study compression expert. Your job is maximum information density.

Output style:
- Bullet points only
- Keywords bolded (use **word**)
- Formulas in [FORMULA: ...]
- No full sentences unless necessary
- No motivational language
- Exam-utility only

Think: marks per minute."""

REVISION_SYSTEM = """You are generating a one-page exam revision sheet. Return valid JSON only."""

REVISION_PROMPT = """Create a revision sheet for: {topic}

Based on this content:
{context}

Return JSON:
{{
  "title": "topic name",
  "formulas": ["formula1", "formula2"],
  "definitions": ["Term: definition"],
  "key_concepts": ["concept bullet"],
  "common_mistakes": ["mistake to avoid"],
  "memory_triggers": ["mnemonic or memory hook"],
  "expected_questions": ["likely exam question"]
}}

Be concise. High signal only."""

SKIP_SYSTEM = """You are a ruthless exam strategist helping a student maximize marks in minimum time.

Classify topics as:
- SAFE TO SKIP: never appeared, low marks, hard to learn
- SKIM ONLY: appeared once, low marks, easy concept
- MUST STUDY: appears frequently, high marks, core concept
- HIGH RISK: appeared every year, high marks

Be conservative. When in doubt, classify higher risk.
Return valid JSON only."""

SKIP_PROMPT = """Analyze these topics from the student's materials and classify them.

Topics and their context:
{context}

Return JSON array:
[
  {{
    "topic": "topic name",
    "category": "SAFE TO SKIP|SKIM ONLY|MUST STUDY|HIGH RISK",
    "reason": "one-line reason based on PYQ frequency and marks",
    "pyq_frequency": number,
    "estimated_marks": number,
    "time_to_study_mins": number
  }}
]"""


def _extract_json(text: str, expect_array: bool = False) -> str:
    clean = text.strip()
    if "```" in clean:
        parts = clean.split("```")
        for p in parts:
            p = p.strip()
            if p.startswith("json"):
                p = p[4:].strip()
            target = "[" if expect_array else "{"
            if p.startswith(target):
                return p
    if expect_array:
        start, end = clean.find("["), clean.rfind("]")
    else:
        start, end = clean.find("{"), clean.rfind("}")
    if start != -1 and end != -1:
        return clean[start:end+1]
    return clean


async def generate_revision_sheet(topic: str, context: str) -> dict:
    response = await run_agent(
        REVISION_SYSTEM,
        [{"role": "user", "content": REVISION_PROMPT.format(
            topic=topic or "full subject",
            context=context[:6000],
        )}],
        max_tokens=2048,
    )
    try:
        return json.loads(_extract_json(response))
    except Exception:
        return {
            "title": topic,
            "formulas": [],
            "definitions": [],
            "key_concepts": [],
            "common_mistakes": [],
            "memory_triggers": [],
            "expected_questions": [],
        }


async def analyze_skip(context: str) -> list[dict]:
    response = await run_agent(
        SKIP_SYSTEM,
        [{"role": "user", "content": SKIP_PROMPT.format(context=context[:8000])}],
        max_tokens=3000,
    )
    try:
        return json.loads(_extract_json(response, expect_array=True))
    except Exception:
        return []


PLAN_SYSTEM = """You are an emergency exam planner. The student may have very little time.

Priorities:
1. HIGH RISK topics first
2. MUST STUDY next
3. Quick wins (short questions, easy definitions)
4. Skip everything else

Be brutally realistic about time constraints.
Return valid JSON only."""

PLAN_PROMPT = """Create an emergency study plan.

Exam in: {hours_available} hours
Preparation level: {prep_level}/10
Topics available:
{topics}

Return JSON:
{{
  "total_hours": number,
  "expected_score_range": "X-Y%",
  "study_blocks": [
    {{
      "time_slot": "9:00 AM - 9:45 AM",
      "activity": "Study|Revision|Break",
      "topic": "topic name",
      "duration_mins": 45,
      "priority": "HIGH|MEDIUM|LOW"
    }}
  ],
  "skip_topics": ["topic to skip"],
  "must_cover": ["absolutely must cover"],
  "tips": ["exam tip 1", "exam tip 2"]
}}"""


async def generate_emergency_plan(hours: float, prep_level: int, topics_context: str) -> dict:
    response = await run_agent(
        PLAN_SYSTEM,
        [{"role": "user", "content": PLAN_PROMPT.format(
            hours_available=hours,
            prep_level=prep_level,
            topics=topics_context[:6000],
        )}],
        max_tokens=3000,
    )
    try:
        return json.loads(_extract_json(response))
    except Exception:
        return {
            "total_hours": hours,
            "expected_score_range": "40-60%",
            "study_blocks": [],
            "skip_topics": [],
            "must_cover": [],
            "tips": ["Focus on most repeated PYQ topics first."],
        }
