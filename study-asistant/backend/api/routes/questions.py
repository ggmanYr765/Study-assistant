from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from agents.prediction import predict_questions
from db.database import get_db
from intelligence.context_builder import build_session_context
from models.schemas import PredictedQuestion, QuestionType, QuestionsResponse

router = APIRouter()


@router.post("/{session_id}/questions/generate", response_model=QuestionsResponse)
async def generate_questions(session_id: UUID, db: AsyncSession = Depends(get_db)):
    row = await db.execute(text("SELECT id FROM sessions WHERE id = :id"), {"id": str(session_id)})
    if not row.fetchone():
        raise HTTPException(404, "Session not found")

    context = await build_session_context(str(session_id), db)
    if not context:
        raise HTTPException(400, "No documents found. Upload study materials first.")

    raw = await predict_questions(context)

    # clear old predictions and store new ones
    await db.execute(
        text("DELETE FROM predicted_questions WHERE session_id = :sid"),
        {"sid": str(session_id)},
    )

    questions: list[PredictedQuestion] = []
    for q in raw:
        try:
            pq = PredictedQuestion(
                question=q.get("question", ""),
                question_type=QuestionType(q.get("question_type", "long")),
                confidence=float(q.get("confidence", 0.5)),
                frequency=int(q.get("frequency", 1)),
                estimated_marks=int(q.get("estimated_marks", 5)),
                answer_outline=q.get("answer_outline", ""),
                topics=q.get("topics", []),
                source_hint=q.get("source_hint", ""),
            )
            await db.execute(
                text("""
                    INSERT INTO predicted_questions
                        (session_id, question, question_type, confidence, frequency,
                         estimated_marks, answer_outline, topics, source_hint)
                    VALUES
                        (:sid, :q, :qtype, :conf, :freq, :marks, :outline, :topics, :hint)
                """),
                {
                    "sid": str(session_id),
                    "q": pq.question,
                    "qtype": pq.question_type.value,
                    "conf": pq.confidence,
                    "freq": pq.frequency,
                    "marks": pq.estimated_marks,
                    "outline": pq.answer_outline,
                    "topics": pq.topics,
                    "hint": pq.source_hint,
                },
            )
            questions.append(pq)
        except Exception:
            continue

    await db.commit()
    return QuestionsResponse(
        session_id=session_id,
        questions=questions,
        generated_at=datetime.now(timezone.utc),
    )


@router.get("/{session_id}/questions", response_model=QuestionsResponse)
async def get_questions(session_id: UUID, db: AsyncSession = Depends(get_db)):
    rows = await db.execute(
        text("""
            SELECT question, question_type, confidence, frequency,
                   estimated_marks, answer_outline, topics, source_hint, created_at
            FROM predicted_questions WHERE session_id = :sid
            ORDER BY confidence DESC
        """),
        {"sid": str(session_id)},
    )
    results = rows.fetchall()
    if not results:
        raise HTTPException(404, "No questions generated yet. Call POST /questions/generate first.")

    questions = [
        PredictedQuestion(
            question=r.question,
            question_type=QuestionType(r.question_type),
            confidence=r.confidence,
            frequency=r.frequency,
            estimated_marks=r.estimated_marks,
            answer_outline=r.answer_outline,
            topics=list(r.topics) if r.topics else [],
            source_hint=r.source_hint or "",
        )
        for r in results
    ]
    return QuestionsResponse(
        session_id=session_id,
        questions=questions,
        generated_at=results[0].created_at,
    )
