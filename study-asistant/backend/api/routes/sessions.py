from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_db
from models.schemas import SessionCreate, SessionOut

router = APIRouter()


@router.post("", response_model=SessionOut, status_code=201)
async def create_session(body: SessionCreate, db: AsyncSession = Depends(get_db)):
    row = await db.execute(
        text("""
            INSERT INTO sessions (name, subject, exam_date)
            VALUES (:name, :subject, :exam_date)
            RETURNING id, name, subject, exam_date, created_at
        """),
        {"name": body.name, "subject": body.subject, "exam_date": body.exam_date},
    )
    await db.commit()
    r = row.fetchone()
    return SessionOut(
        id=r.id, name=r.name, subject=r.subject,
        exam_date=r.exam_date, created_at=r.created_at,
    )


@router.get("", response_model=list[SessionOut])
async def list_sessions(db: AsyncSession = Depends(get_db)):
    rows = await db.execute(
        text("SELECT id, name, subject, exam_date, created_at FROM sessions ORDER BY created_at DESC")
    )
    return [
        SessionOut(id=r.id, name=r.name, subject=r.subject,
                   exam_date=r.exam_date, created_at=r.created_at)
        for r in rows
    ]


@router.get("/{session_id}", response_model=SessionOut)
async def get_session(session_id: UUID, db: AsyncSession = Depends(get_db)):
    row = await db.execute(
        text("SELECT id, name, subject, exam_date, created_at FROM sessions WHERE id = :id"),
        {"id": str(session_id)},
    )
    r = row.fetchone()
    if not r:
        raise HTTPException(404, "Session not found")
    return SessionOut(id=r.id, name=r.name, subject=r.subject,
                      exam_date=r.exam_date, created_at=r.created_at)


@router.delete("/{session_id}", status_code=204)
async def delete_session(session_id: UUID, db: AsyncSession = Depends(get_db)):
    await db.execute(text("DELETE FROM sessions WHERE id = :id"), {"id": str(session_id)})
    await db.commit()
