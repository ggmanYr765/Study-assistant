import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from db.database import init_db
from api.routes import sessions, upload, chat, analyze, questions, skip, plan, revision


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    os.makedirs("uploads", exist_ok=True)
    yield


app = FastAPI(title="Study Assistant API", version="1.0.0", lifespan=lifespan)

_raw_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000")
_origins = [o.strip() for o in _raw_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(sessions.router, prefix="/api/v1/sessions", tags=["sessions"])
app.include_router(upload.router, prefix="/api/v1/sessions", tags=["upload"])
app.include_router(chat.router, prefix="/api/v1/sessions", tags=["chat"])
app.include_router(analyze.router, prefix="/api/v1/sessions", tags=["analyze"])
app.include_router(questions.router, prefix="/api/v1/sessions", tags=["questions"])
app.include_router(skip.router, prefix="/api/v1/sessions", tags=["skip"])
app.include_router(plan.router, prefix="/api/v1/sessions", tags=["plan"])
app.include_router(revision.router, prefix="/api/v1/sessions", tags=["revision"])


@app.get("/health")
async def health():
    return {"status": "ok"}
