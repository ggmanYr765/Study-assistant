from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from agents.summarization import analyze_skip
from db.database import get_db
from intelligence.context_builder import build_session_context
from models.schemas import SkipCategory, SkipResponse, TopicAnalysis

router = APIRouter()


@router.post("/{session_id}/skip/analyze", response_model=SkipResponse)
async def generate_skip_analysis(session_id: UUID, db: AsyncSession = Depends(get_db)):
    row = await db.execute(text("SELECT id FROM sessions WHERE id = :id"), {"id": str(session_id)})
    if not row.fetchone():
        raise HTTPException(404, "Session not found")

    context = await build_session_context(str(session_id), db)
    if not context:
        raise HTTPException(400, "No documents found. Upload study materials first.")

    raw = await analyze_skip(context)

    await db.execute(
        text("DELETE FROM skip_analysis WHERE session_id = :sid"),
        {"sid": str(session_id)},
    )

    topics: list[TopicAnalysis] = []
    for t in raw:
        try:
            ta = TopicAnalysis(
                topic=t.get("topic", ""),
                category=SkipCategory(t.get("category", "SKIM ONLY")),
                reason=t.get("reason", ""),
                pyq_frequency=int(t.get("pyq_frequency", 0)),
                estimated_marks=int(t.get("estimated_marks", 0)),
                time_to_study_mins=int(t.get("time_to_study_mins", 30)),
            )
            await db.execute(
                text("""
                    INSERT INTO skip_analysis
                        (session_id, topic, category, reason, pyq_frequency,
                         estimated_marks, time_to_study_mins)
                    VALUES (:sid, :topic, :cat, :reason, :freq, :marks, :time)
                """),
                {
                    "sid": str(session_id),
                    "topic": ta.topic,
                    "cat": ta.category.value,
                    "reason": ta.reason,
                    "freq": ta.pyq_frequency,
                    "marks": ta.estimated_marks,
                    "time": ta.time_to_study_mins,
                },
            )
            topics.append(ta)
        except Exception:
            continue

    await db.commit()

    must = sum(1 for t in topics if t.category in (SkipCategory.must_study, SkipCategory.high_risk))
    skip = sum(1 for t in topics if t.category == SkipCategory.safe_to_skip)
    summary = f"{must} topics must be studied. {skip} topics are safe to skip."

    return SkipResponse(
        session_id=session_id,
        topics=topics,
        summary=summary,
        generated_at=datetime.now(timezone.utc),
    )


@router.get("/{session_id}/skip", response_model=SkipResponse)
async def get_skip_analysis(session_id: UUID, db: AsyncSession = Depends(get_db)):
    rows = await db.execute(
        text("""
            SELECT topic, category, reason, pyq_frequency, estimated_marks,
                   time_to_study_mins, created_at
            FROM skip_analysis WHERE session_id = :sid
            ORDER BY
                CASE category
                    WHEN 'HIGH RISK' THEN 1
                    WHEN 'MUST STUDY' THEN 2
                    WHEN 'SKIM ONLY' THEN 3
                    WHEN 'SAFE TO SKIP' THEN 4
                END
        """),
        {"sid": str(session_id)},
    )
    results = rows.fetchall()
    if not results:
        raise HTTPException(404, "No skip analysis found. Call POST /skip/analyze first.")

    topics = [
        TopicAnalysis(
            topic=r.topic,
            category=SkipCategory(r.category),
            reason=r.reason,
            pyq_frequency=r.pyq_frequency,
            estimated_marks=r.estimated_marks,
            time_to_study_mins=r.time_to_study_mins,
        )
        for r in results
    ]
    must = sum(1 for t in topics if t.category in (SkipCategory.must_study, SkipCategory.high_risk))
    skip = sum(1 for t in topics if t.category == SkipCategory.safe_to_skip)

    return SkipResponse(
        session_id=session_id,
        topics=topics,
        summary=f"{must} topics must be studied. {skip} topics are safe to skip.",
        generated_at=results[0].created_at,
    )
