"""Build a rich context summary from all chunks in a session for analysis agents."""
from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def build_session_context(session_id: str, db: AsyncSession, max_chars: int = 12000) -> str:
    """
    Assemble session content for analysis agents.
    Priority order: handwritten > professor > pyq > textbook > other.
    """
    rows = await db.execute(
        text("""
            SELECT c.content, c.heading, c.chunk_type, c.source_priority,
                   d.doc_type, d.filename
            FROM chunks c
            JOIN documents d ON d.id = c.document_id
            WHERE c.session_id = :sid
            ORDER BY c.source_priority ASC, c.id ASC
        """),
        {"sid": str(session_id)},
    )
    chunks = [dict(r._mapping) for r in rows]

    if not chunks:
        return ""

    parts: list[str] = []
    total = 0

    # Group by doc_type for structured context
    by_type: dict[str, list[dict]] = {}
    for c in chunks:
        by_type.setdefault(c["doc_type"], []).append(c)

    type_order = ["handwritten", "professor", "pyq", "syllabus", "textbook", "other"]
    for dtype in type_order:
        if dtype not in by_type:
            continue
        parts.append(f"\n=== {dtype.upper()} MATERIAL ===")
        for c in by_type[dtype]:
            snippet = c["content"][:600]
            if c["heading"]:
                line = f"[{c['chunk_type']}] {c['heading']}: {snippet}"
            else:
                line = f"[{c['chunk_type']}] {snippet}"
            parts.append(line)
            total += len(line)
            if total >= max_chars:
                break
        if total >= max_chars:
            break

    return "\n".join(parts)


async def get_topic_list(session_id: str, db: AsyncSession) -> list[str]:
    """Extract unique topics/headings from session chunks."""
    rows = await db.execute(
        text("""
            SELECT DISTINCT heading FROM chunks
            WHERE session_id = :sid AND heading IS NOT NULL AND heading != ''
            LIMIT 100
        """),
        {"sid": str(session_id)},
    )
    return [r[0] for r in rows if r[0]]
