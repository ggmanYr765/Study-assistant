# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Run with Docker (recommended)
```bash
cp .env.example .env   # add ANTHROPIC_API_KEY and VOYAGE_API_KEY
docker compose up --build
```
Frontend: http://localhost:3000 | Backend API: http://localhost:8000

### Run locally (without Docker)

**Backend**
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp ../.env.example .env   # fill in keys + local DATABASE_URL
uvicorn main:app --reload --port 8000
```

**Frontend**
```bash
cd frontend
npm install
npm run dev   # http://localhost:3000
```

**Database** (requires PostgreSQL with pgvector extension)
```bash
psql -U postgres -c "CREATE DATABASE studyassistant;"
```
Tables are auto-created on first backend startup via `db/database.py:init_db`.

### Lint / type-check
```bash
# Frontend
cd frontend && npm run lint

# Backend (no linter configured; use ruff if needed)
pip install ruff && ruff check backend/
```

---

## Architecture

### Tech Stack
| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 14 (App Router), Tailwind CSS |
| Backend | Python FastAPI (async) |
| Vector DB | PostgreSQL + pgvector |
| Embeddings | sentence-transformers `all-MiniLM-L6-v2` (local, 384-dim, no API key) |
| LLM | DeepSeek API — OpenAI-compatible (`deepseek-chat`) |
| OCR | DeepSeek vision API (multimodal) |
| PDF parsing | pymupdf (fitz) |

### Backend (`backend/`)

**Ingestion pipeline** — triggered as a FastAPI `BackgroundTask` on file upload:
1. `ingestion/parser.py` — parse PDF (pymupdf) or image files into `ParsedDocument`
2. `ingestion/ocr.py` — run Claude vision OCR on image-heavy / handwritten pages
3. `ingestion/chunker.py` — semantic chunking that preserves headings, formulas, Q&A structure
4. `ingestion/embedder.py` — Voyage AI batch embedding, stored as `vector(1024)` in pgvector

**AI agents** (`agents/`) — each is a single-purpose Claude call with a cached system prompt:
- `base.py` — `run_agent()` and `stream_agent()` with prompt caching via `cache_control: ephemeral`
- `rag.py` — retrieves top-K chunks by cosine similarity, builds context ordered by source priority, streams response
- `prediction.py` — predicts probable exam questions from session context
- `summarization.py` — generates revision sheets, skip analysis, and emergency plans

**Source priority** — lower number = higher trust in retrieval:
1. handwritten → 2. professor slides → 3. PYQ/syllabus → 4. textbook → 5. other

**Intelligence layer** (`intelligence/`):
- `context_builder.py` — assembles full session context for analysis agents, grouped by doc_type in priority order

**API routes** (`api/routes/`) — all prefixed `/api/v1/sessions/{session_id}/`:
- `POST /` → create session, `GET /` → list, `GET /{id}` → get, `DELETE /{id}` → delete
- `POST /{id}/documents` → upload + trigger ingestion background task
- `POST /{id}/chat` → RAG chat (blocking), `POST /{id}/chat/stream` → SSE streaming
- `POST /{id}/analyze` → full exam analysis (questions + skip + revision in one call)
- `POST /{id}/questions/generate` → generate + store predicted questions
- `GET /{id}/questions` → fetch stored questions
- `POST /{id}/skip/analyze` → generate + store skip analysis
- `GET /{id}/skip` → fetch stored skip analysis
- `POST /{id}/revision` → generate revision sheet (not stored)
- `POST /{id}/plan` → generate emergency study plan (not stored)

### Frontend (`frontend/`)

Next.js App Router structure:
- `app/page.tsx` — home: create/list/delete sessions
- `app/session/[id]/layout.tsx` — sidebar navigation shared across all session pages
- `app/session/[id]/page.tsx` — upload documents + status polling
- `app/session/[id]/chat/page.tsx` — streaming RAG chat with SSE
- `app/session/[id]/exam-mode/page.tsx` — one-click full analysis
- `app/session/[id]/questions/page.tsx` — predicted questions with filter tabs
- `app/session/[id]/skip/page.tsx` — skip analysis grouped by category
- `app/session/[id]/plan/page.tsx` — emergency study plan form + schedule

`lib/api.ts` — typed client that proxies all calls through Next.js rewrites to the backend.

`next.config.ts` rewrites `/api/v1/*` → `NEXT_PUBLIC_API_URL/api/v1/*` (defaults to `http://localhost:8000`).

### Database schema (auto-migrated on startup)
- `sessions` — study sessions with name, subject, exam_date
- `documents` — uploaded files with doc_type, source_priority, status (processing|ready|error)
- `chunks` — text chunks with `vector(1024)` embedding, heading, chunk_type, source_priority
- `predicted_questions` — stored predictions from the question predictor
- `skip_analysis` — stored topic classifications

### Env vars required
```
DEEPSEEK_API_KEY    # DeepSeek API (https://platform.deepseek.com)
DATABASE_URL        # PostgreSQL asyncpg URL
```
Embeddings run locally via sentence-transformers — no extra API key needed.

---

## Product Philosophy

Every feature optimizes for **marks per minute**. Source priority (handwritten > professor > PYQ > textbook) must be respected in all retrieval. Never hallucinate or fabricate source material — cite only what is in uploaded documents. The five flagship features: Exam Tomorrow Mode, Source-Grounded Chat, PYQ Intelligence, Skip Analyzer, Emergency Planner.
