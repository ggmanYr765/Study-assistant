"""Full exam analysis: questions + skip + revision in one shot."""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from agents.prediction import predict_questions
from agents.summarization import analyze_skip, generate_revision_sheet
from db.database import get_db
from intelligence.context_builder import build_session_context
from models.schemas import (
    ExamAnalysis, PredictedQuestion, QuestionType,
    RevisionSheet, SkipCategory, TopicAnalysis,
)

router = APIRouter()


@router.post("/{session_id}/analyze", response_model=ExamAnalysis)
async def full_exam_analysis(session_id: UUID, db: AsyncSession = Depends(get_db)):
    row = await db.execute(text("SELECT id, name FROM sessions WHERE id = :id"), {"id": str(session_id)})
    session = row.fetchone()
    if not session:
        raise HTTPException(404, "Session not found")

    context = await build_session_context(str(session_id), db)
    if not context:
        raise HTTPException(400, "No documents found. Upload study materials first.")

    # run all three agents (could be parallelized with asyncio.gather in future)
    raw_questions = await predict_questions(context)
    raw_skip = await analyze_skip(context)
    raw_revision = await generate_revision_sheet("", context)

    questions: list[PredictedQuestion] = []
    for q in raw_questions:
        try:
            questions.append(PredictedQuestion(
                question=q.get("question", ""),
                question_type=QuestionType(q.get("question_type", "long")),
                confidence=float(q.get("confidence", 0.5)),
                frequency=int(q.get("frequency", 1)),
                estimated_marks=int(q.get("estimated_marks", 5)),
                answer_outline=q.get("answer_outline", ""),
                topics=q.get("topics", []),
                source_hint=q.get("source_hint", ""),
            ))
        except Exception:
            continue

    skip_topics: list[TopicAnalysis] = []
    for t in raw_skip:
        try:
            skip_topics.append(TopicAnalysis(
                topic=t.get("topic", ""),
                category=SkipCategory(t.get("category", "SKIM ONLY")),
                reason=t.get("reason", ""),
                pyq_frequency=int(t.get("pyq_frequency", 0)),
                estimated_marks=int(t.get("estimated_marks", 0)),
                time_to_study_mins=int(t.get("time_to_study_mins", 30)),
            ))
        except Exception:
            continue

    revision = RevisionSheet(**raw_revision) if raw_revision else RevisionSheet(
        title=session.name, formulas=[], definitions=[], key_concepts=[],
        common_mistakes=[], memory_triggers=[], expected_questions=[],
    )

    must = sum(1 for t in skip_topics if t.category in (SkipCategory.must_study, SkipCategory.high_risk))
    safe = sum(1 for t in skip_topics if t.category == SkipCategory.safe_to_skip)

    return ExamAnalysis(
        questions=questions,
        skip_analysis=skip_topics,
        revision_sheet=revision,
        summary=f"Found {len(questions)} probable questions. {must} topics must be studied, {safe} safe to skip.",
    )
