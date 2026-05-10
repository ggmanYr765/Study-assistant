from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from agents.summarization import generate_emergency_plan
from db.database import get_db
from intelligence.context_builder import build_session_context
from models.schemas import EmergencyPlan, PlanRequest, StudyBlock

router = APIRouter()


@router.post("/{session_id}/plan", response_model=EmergencyPlan)
async def get_emergency_plan(
    session_id: UUID,
    body: PlanRequest,
    db: AsyncSession = Depends(get_db),
):
    row = await db.execute(text("SELECT id FROM sessions WHERE id = :id"), {"id": str(session_id)})
    if not row.fetchone():
        raise HTTPException(404, "Session not found")

    context = await build_session_context(str(session_id), db)
    if not context:
        raise HTTPException(400, "No documents found. Upload study materials first.")

    raw = await generate_emergency_plan(body.available_hours, body.preparation_level, context)

    blocks = [StudyBlock(**b) for b in raw.get("study_blocks", [])]
    return EmergencyPlan(
        total_hours=raw.get("total_hours", body.available_hours),
        expected_score_range=raw.get("expected_score_range", "Unknown"),
        study_blocks=blocks,
        skip_topics=raw.get("skip_topics", []),
        must_cover=raw.get("must_cover", []),
        tips=raw.get("tips", []),
    )
