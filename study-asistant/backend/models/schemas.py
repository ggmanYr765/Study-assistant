from __future__ import annotations
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel


class DocType(str, Enum):
    handwritten = "handwritten"
    professor = "professor"
    pyq = "pyq"
    textbook = "textbook"
    syllabus = "syllabus"
    other = "other"


class QuestionType(str, Enum):
    long = "long"
    short = "short"
    derivation = "derivation"
    numerical = "numerical"


class SkipCategory(str, Enum):
    safe_to_skip = "SAFE TO SKIP"
    skim_only = "SKIM ONLY"
    must_study = "MUST STUDY"
    high_risk = "HIGH RISK"


# ── Session ──────────────────────────────────────────────────────────────────

class SessionCreate(BaseModel):
    name: str
    subject: str = ""
    exam_date: str = ""  # ISO date string


class SessionOut(BaseModel):
    id: UUID
    name: str
    subject: str
    exam_date: str
    created_at: datetime

    class Config:
        from_attributes = True


# ── Documents ─────────────────────────────────────────────────────────────────

class DocumentOut(BaseModel):
    id: UUID
    session_id: UUID
    filename: str
    doc_type: DocType
    page_count: int
    status: str
    uploaded_at: datetime

    class Config:
        from_attributes = True


# ── Chat ──────────────────────────────────────────────────────────────────────

class ChatMessage(BaseModel):
    role: str  # "user" | "assistant"
    content: str


class ChatRequest(BaseModel):
    message: str
    history: list[ChatMessage] = []


class SourceChunk(BaseModel):
    content: str
    source: str
    doc_type: str
    page: int | None = None
    relevance: float


class ChatResponse(BaseModel):
    answer: str
    sources: list[SourceChunk]
    confidence: str  # "high" | "medium" | "low"


# ── Questions ─────────────────────────────────────────────────────────────────

class PredictedQuestion(BaseModel):
    question: str
    question_type: QuestionType
    confidence: float  # 0-1
    frequency: int
    estimated_marks: int
    answer_outline: str
    topics: list[str]
    source_hint: str = ""


class QuestionsResponse(BaseModel):
    session_id: UUID
    questions: list[PredictedQuestion]
    generated_at: datetime


# ── Skip Analysis ─────────────────────────────────────────────────────────────

class TopicAnalysis(BaseModel):
    topic: str
    category: SkipCategory
    reason: str
    pyq_frequency: int
    estimated_marks: int
    time_to_study_mins: int


class SkipResponse(BaseModel):
    session_id: UUID
    topics: list[TopicAnalysis]
    summary: str
    generated_at: datetime


# ── Revision Sheet ────────────────────────────────────────────────────────────

class RevisionSheet(BaseModel):
    title: str
    formulas: list[str]
    definitions: list[str]
    key_concepts: list[str]
    common_mistakes: list[str]
    memory_triggers: list[str]
    expected_questions: list[str]


class RevisionRequest(BaseModel):
    topic: str = ""  # empty = full subject


# ── Emergency Plan ────────────────────────────────────────────────────────────

class PlanRequest(BaseModel):
    exam_date: str  # ISO datetime
    preparation_level: int  # 1-10
    available_hours: float


class StudyBlock(BaseModel):
    time_slot: str
    activity: str
    topic: str
    duration_mins: int
    priority: str


class EmergencyPlan(BaseModel):
    total_hours: float
    expected_score_range: str
    study_blocks: list[StudyBlock]
    skip_topics: list[str]
    must_cover: list[str]
    tips: list[str]


# ── Full Exam Analysis ────────────────────────────────────────────────────────

class ExamAnalysis(BaseModel):
    questions: list[PredictedQuestion]
    skip_analysis: list[TopicAnalysis]
    revision_sheet: RevisionSheet
    summary: str
