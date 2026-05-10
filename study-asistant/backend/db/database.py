from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import text

from config import settings

engine = create_async_engine(settings.database_url, echo=False, pool_pre_ping=True)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session


async def init_db():
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\""))
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))

        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS sessions (
                id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                name TEXT NOT NULL,
                subject TEXT NOT NULL DEFAULT '',
                exam_date TEXT NOT NULL DEFAULT '',
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
        """))

        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS documents (
                id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
                filename TEXT NOT NULL,
                doc_type TEXT NOT NULL DEFAULT 'other',
                source_priority INTEGER NOT NULL DEFAULT 5,
                page_count INTEGER NOT NULL DEFAULT 0,
                status TEXT NOT NULL DEFAULT 'processing',
                uploaded_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
        """))

        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS chunks (
                id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
                session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
                content TEXT NOT NULL,
                heading TEXT,
                chunk_type TEXT DEFAULT 'text',
                source_priority INTEGER NOT NULL DEFAULT 5,
                page_number INTEGER,
                embedding vector(384),
                metadata JSONB NOT NULL DEFAULT '{}'
            )
        """))

        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS predicted_questions (
                id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
                question TEXT NOT NULL,
                question_type TEXT NOT NULL,
                confidence FLOAT NOT NULL DEFAULT 0.5,
                frequency INTEGER NOT NULL DEFAULT 1,
                estimated_marks INTEGER NOT NULL DEFAULT 5,
                answer_outline TEXT NOT NULL DEFAULT '',
                topics TEXT[] NOT NULL DEFAULT '{}',
                source_hint TEXT NOT NULL DEFAULT '',
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
        """))

        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS skip_analysis (
                id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
                topic TEXT NOT NULL,
                category TEXT NOT NULL,
                reason TEXT NOT NULL DEFAULT '',
                pyq_frequency INTEGER NOT NULL DEFAULT 0,
                estimated_marks INTEGER NOT NULL DEFAULT 0,
                time_to_study_mins INTEGER NOT NULL DEFAULT 30,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
        """))

        # indexes (ignore if exist)
        for idx_sql in [
            "CREATE INDEX IF NOT EXISTS idx_chunks_session ON chunks(session_id)",
            "CREATE INDEX IF NOT EXISTS idx_chunks_priority ON chunks(session_id, source_priority)",
            "CREATE INDEX IF NOT EXISTS idx_docs_session ON documents(session_id)",
            "CREATE INDEX IF NOT EXISTS idx_questions_session ON predicted_questions(session_id)",
            "CREATE INDEX IF NOT EXISTS idx_skip_session ON skip_analysis(session_id)",
        ]:
            await conn.execute(text(idx_sql))
