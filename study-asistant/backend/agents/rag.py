"""Retrieval-Augmented Generation agent."""
from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from agents.base import run_agent, stream_agent
from ingestion.embedder import embed_query
from models.schemas import ChatMessage, ChatResponse, SourceChunk

RAG_SYSTEM = """You are an expert study assistant for exam preparation. You ONLY answer using the provided source excerpts.

Rules:
- Ground EVERY claim in the provided sources
- Cite sources as [Source N] inline
- If sources don't cover the question, say: "I couldn't find this in your uploaded materials. Here's what I do have: [show closest source]"
- Never hallucinate or fabricate content
- Optimize answers for exam utility: keywords, structure, marks
- Prefer handwritten notes and professor material over textbooks
- Be concise. Exam-focused. No motivational fluff."""


async def retrieve_chunks(
    session_id: str,
    query: str,
    db: AsyncSession,
    top_k: int = 8,
) -> list[dict]:
    query_vec = embed_query(query)
    vec_str = "[" + ",".join(str(x) for x in query_vec) + "]"

    rows = await db.execute(
        text("""
            SELECT c.id, c.content, c.heading, c.chunk_type, c.source_priority,
                   c.page_number, c.metadata, d.filename, d.doc_type,
                   1 - (c.embedding <=> CAST(:vec AS vector)) AS similarity
            FROM chunks c
            JOIN documents d ON d.id = c.document_id
            WHERE c.session_id = :sid
              AND c.embedding IS NOT NULL
            ORDER BY c.embedding <=> CAST(:vec AS vector)
            LIMIT :k
        """),
        {"sid": str(session_id), "vec": vec_str, "k": top_k},
    )
    return [dict(r._mapping) for r in rows]


def build_context(chunks: list[dict]) -> str:
    # sort by source priority (lower = more trusted), then similarity
    sorted_chunks = sorted(chunks, key=lambda c: (c["source_priority"], -c["similarity"]))
    parts = []
    for i, c in enumerate(sorted_chunks, 1):
        header = f"[Source {i}] {c['filename']} (p.{c['page_number'] or '?'}) [{c['doc_type']}]"
        parts.append(f"{header}\n{c['content']}")
    return "\n\n---\n\n".join(parts)


async def rag_chat(
    session_id: str,
    question: str,
    history: list[ChatMessage],
    db: AsyncSession,
) -> ChatResponse:
    chunks = await retrieve_chunks(session_id, question, db)

    if not chunks:
        return ChatResponse(
            answer="No study materials found for this session. Please upload your notes, syllabus, or previous year papers first.",
            sources=[],
            confidence="low",
        )

    context = build_context(chunks)
    messages = [
        *[{"role": m.role, "content": m.content} for m in history[-6:]],
        {
            "role": "user",
            "content": f"Source Materials:\n{context}\n\nQuestion: {question}",
        },
    ]

    answer = await run_agent(RAG_SYSTEM, messages)

    # assess confidence by average similarity
    avg_sim = sum(c["similarity"] for c in chunks) / len(chunks)
    confidence = "high" if avg_sim > 0.75 else "medium" if avg_sim > 0.55 else "low"

    sources = [
        SourceChunk(
            content=c["content"][:300],
            source=c["filename"],
            doc_type=c["doc_type"],
            page=c["page_number"],
            relevance=round(float(c["similarity"]), 3),
        )
        for c in chunks[:5]
    ]

    return ChatResponse(answer=answer, sources=sources, confidence=confidence)


async def rag_stream(
    session_id: str,
    question: str,
    history: list[ChatMessage],
    db: AsyncSession,
):
    """Yields SSE-formatted chunks for streaming."""
    chunks = await retrieve_chunks(session_id, question, db)

    if not chunks:
        yield "data: No study materials found. Please upload documents first.\n\n"
        return

    context = build_context(chunks)
    messages = [
        *[{"role": m.role, "content": m.content} for m in history[-6:]],
        {
            "role": "user",
            "content": f"Source Materials:\n{context}\n\nQuestion: {question}",
        },
    ]

    async for delta in stream_agent(RAG_SYSTEM, messages):
        yield f"data: {delta}\n\n"

    yield "data: [DONE]\n\n"
