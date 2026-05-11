from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/studyassistant"
    deepseek_api_key: str
    gemini_api_key: str = ""
    hf_token: str = ""
    openrouter_api_key: str = ""
    upload_dir: str = "uploads"  # temp dir for processing before R2 upload
    # Cloudflare R2
    r2_account_id: str = ""
    r2_access_key_id: str = ""
    r2_secret_access_key: str = ""
    r2_bucket: str = "study-assistant"
    source_priorities: dict = {
        "handwritten": 1,
        "professor": 2,
        "pyq": 3,
        "syllabus": 3,
        "textbook": 4,
        "other": 5,
    }
    # DeepSeek models (OpenAI-compatible API)
    fast_model: str = "deepseek-chat"
    smart_model: str = "deepseek-chat"
    # Local sentence-transformers embedding model
    embedding_model: str = "all-MiniLM-L6-v2"
    embedding_dim: int = 384

    class Config:
        env_file = ".env"


settings = Settings()
