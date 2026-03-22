from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Ollama — runs locally, no API key needed
    llm_base_url: str = "http://ollama:11434/v1"
    openai_model: str = "llama3.2:3b"
    embedding_model: str = "all-MiniLM-L6-v2"  # local sentence-transformers, no API cost

    # Qdrant
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_collection: str = "legaldoc"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # PostgreSQL
    database_url: str

    # Auth
    jwt_secret: str = "change-me-in-production-use-a-long-random-string"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24  # 24 hours

    # Google OAuth (optional)
    google_client_id: str = ""
    google_client_secret: str = ""
    frontend_url: str = "http://localhost:3000"

    # SMTP — optional, for password reset emails
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = ""

    # App
    app_env: str = "development"
    max_file_size_mb: int = 50
    chunk_size: int = 512
    chunk_overlap: int = 64
    top_k_retrieval: int = 6
    confidence_threshold: float = 0.72

    class Config:
        env_file = ".env"


settings = Settings()
