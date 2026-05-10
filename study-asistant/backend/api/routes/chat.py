from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from agents.rag import rag_chat, rag_stream
from db.database import get_db
from models.schemas import ChatRequest, ChatResponse

router = APIRouter()


@router.post("/{session_id}/chat", response_model=ChatResponse)
async def chat(session_id: UUID, body: ChatRequest, db: AsyncSession = Depends(get_db)):
    row = await db.execute(text("SELECT id FROM sessions WHERE id = :id"), {"id": str(session_id)})
    if not row.fetchone():
        raise HTTPException(404, "Session not found")
    return await rag_chat(str(session_id), body.message, body.history, db)


@router.post("/{session_id}/chat/stream")
async def chat_stream(session_id: UUID, body: ChatRequest, db: AsyncSession = Depends(get_db)):
    row = await db.execute(text("SELECT id FROM sessions WHERE id = :id"), {"id": str(session_id)})
    if not row.fetchone():
        raise HTTPException(404, "Session not found")

    return StreamingResponse(
        rag_stream(str(session_id), body.message, body.history, db),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
