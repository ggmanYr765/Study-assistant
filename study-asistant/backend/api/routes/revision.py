from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from agents.summarization import generate_revision_sheet
from db.database import get_db
from intelligence.context_builder import build_session_context
from models.schemas import RevisionRequest, RevisionSheet

router = APIRouter()


@router.post("/{session_id}/revision", response_model=RevisionSheet)
async def get_revision_sheet(
    session_id: UUID,
    body: RevisionRequest,
    db: AsyncSession = Depends(get_db),
):
    row = await db.execute(text("SELECT id FROM sessions WHERE id = :id"), {"id": str(session_id)})
    if not row.fetchone():
        raise HTTPException(404, "Session not found")

    context = await build_session_context(str(session_id), db)
    if not context:
        raise HTTPException(400, "No documents found. Upload study materials first.")

    raw = await generate_revision_sheet(body.topic, context)
    return RevisionSheet(**raw)
