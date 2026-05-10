"""File upload and ingestion pipeline."""
from __future__ import annotations
import os
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from db.database import get_db, AsyncSessionLocal
from ingestion.chunker import chunk_document
from ingestion.embedder import embed_texts
from ingestion.ocr import ocr_images
from ingestion.parser import parse_file
from models.schemas import DocType, DocumentOut
from storage.r2 import upload_file as r2_upload, delete_file as r2_delete

router = APIRouter()

SOURCE_PRIORITY = {
    "handwritten": 1,
    "professor": 2,
    "pyq": 3,
    "syllabus": 3,
    "textbook": 4,
    "other": 5,
}


@router.post("/{session_id}/documents", response_model=DocumentOut, status_code=201)
async def upload_document(
    session_id: UUID,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    doc_type: str = Form("other"),
    db: AsyncSession = Depends(get_db),
):
    # verify session exists
    row = await db.execute(text("SELECT id FROM sessions WHERE id = :id"), {"id": str(session_id)})
    if not row.fetchone():
        raise HTTPException(404, "Session not found")

    # save file
    upload_dir = Path(settings.upload_dir) / str(session_id)
    upload_dir.mkdir(parents=True, exist_ok=True)
    file_path = upload_dir / file.filename
    content = await file.read()
    file_path.write_bytes(content)

    priority = SOURCE_PRIORITY.get(doc_type, 5)
    row = await db.execute(
        text("""
            INSERT INTO documents (session_id, filename, doc_type, source_priority, status)
            VALUES (:sid, :fname, :dtype, :priority, 'processing')
            RETURNING id, session_id, filename, doc_type, source_priority, page_count, status, uploaded_at
        """),
        {"sid": str(session_id), "fname": file.filename, "dtype": doc_type, "priority": priority},
    )
    await db.commit()
    doc = row.fetchone()

    r2_key = f"{session_id}/{doc.id}/{file.filename}"
    background_tasks.add_task(ingest_document, str(doc.id), str(session_id), str(file_path), doc_type, priority, r2_key)

    return DocumentOut(
        id=doc.id, session_id=doc.session_id, filename=doc.filename,
        doc_type=DocType(doc.doc_type), page_count=doc.page_count,
        status=doc.status, uploaded_at=doc.uploaded_at,
    )


@router.get("/{session_id}/documents", response_model=list[DocumentOut])
async def list_documents(session_id: UUID, db: AsyncSession = Depends(get_db)):
    rows = await db.execute(
        text("""
            SELECT id, session_id, filename, doc_type, source_priority, page_count, status, uploaded_at
            FROM documents WHERE session_id = :sid ORDER BY uploaded_at DESC
        """),
        {"sid": str(session_id)},
    )
    return [
        DocumentOut(
            id=r.id, session_id=r.session_id, filename=r.filename,
            doc_type=DocType(r.doc_type), page_count=r.page_count,
            status=r.status, uploaded_at=r.uploaded_at,
        )
        for r in rows
    ]


async def ingest_document(doc_id: str, session_id: str, file_path: str, doc_type: str, priority: int, r2_key: str = ""):
    """Background ingestion: parse → OCR → chunk → embed → store."""
    async with AsyncSessionLocal() as db:
        try:
            parsed = parse_file(file_path)

            # prefer extracted text; only OCR when page has no text at all
            page_texts: dict[int, str] = {}
            for page in parsed.pages:
                if page.text and len(page.text.strip()) > 30:
                    page_texts[page.page_number] = page.text
                elif page.images:
                    page_texts[page.page_number] = ocr_images(page.images)

            chunks = chunk_document(parsed, page_texts)

            if not chunks:
                await db.execute(
                    text("UPDATE documents SET status='ready', page_count=:pc WHERE id=:id"),
                    {"pc": parsed.page_count, "id": doc_id},
                )
                await db.commit()
                return

            # embed all chunks in one batch
            texts = [c.content for c in chunks]
            embeddings = embed_texts(texts)

            for chunk, emb in zip(chunks, embeddings):
                vec_str = "[" + ",".join(str(x) for x in emb) + "]"
                await db.execute(
                    text("""
                        INSERT INTO chunks
                            (document_id, session_id, content, heading, chunk_type,
                             source_priority, page_number, embedding, metadata)
                        VALUES
                            (:doc_id, :sid, :content, :heading, :ctype,
                             :priority, :page, CAST(:emb AS vector), CAST(:meta AS jsonb))
                    """),
                    {
                        "doc_id": doc_id,
                        "sid": session_id,
                        "content": chunk.content,
                        "heading": chunk.heading or None,
                        "ctype": chunk.chunk_type,
                        "priority": priority,
                        "page": chunk.page_number,
                        "emb": vec_str,
                        "meta": "{}",
                    },
                )

            await db.execute(
                text("UPDATE documents SET status='ready', page_count=:pc WHERE id=:id"),
                {"pc": parsed.page_count, "id": doc_id},
            )
            await db.commit()

            # upload to R2 then delete local temp file
            if r2_key and settings.r2_account_id:
                r2_upload(file_path, r2_key)
                Path(file_path).unlink(missing_ok=True)

        except Exception as e:
            await db.execute(
                text("UPDATE documents SET status='error' WHERE id=:id"),
                {"id": doc_id},
            )
            await db.commit()
            raise
