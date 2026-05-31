import os

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Document Automation RAG API"
    API_V1_STR: str = "/api/v1"

    # Generative / VLM Settings
    OPENAI_BASE_URL: str = os.getenv("OPENAI_BASE_URL", "http://localhost:11434/v1")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_GENERATIVE_MODEL: str = os.getenv("OPENAI_GENERATIVE_MODEL", "llama3.2-vision")

    # Embedding Settings (defaults to OPENAI_BASE_URL if not set, or local Ollama)
    OPENAI_EMBEDDING_BASE_URL: str = os.getenv(
        "OPENAI_EMBEDDING_BASE_URL", os.getenv("OPENAI_BASE_URL", "http://localhost:11434/v1")
    )
    OPENAI_EMBEDDING_API_KEY: str = os.getenv("OPENAI_EMBEDDING_API_KEY", os.getenv("OPENAI_API_KEY", ""))
    OPENAI_EMBEDDING_MODEL: str = os.getenv("OPENAI_EMBEDDING_MODEL", "nomic-embed-text")

    # Database Settings
    POSTGRES_URL: str | None = os.getenv("POSTGRES_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/rag_db")

    # Evaluation Judge Settings
    JUDGE_LLM_BASE_URL: str | None = os.getenv("OPENAI_JUDGE_LLM_BASE_URL")
    JUDGE_LLM_API_KEY: str | None = os.getenv("OPENAI_JUDGE_LLM_API_KEY")
    JUDGE_LLM_MODEL: str | None = os.getenv("OPENAI_JUDGE_LLM_MODEL")

    # Storage
    UPLOAD_DIR: str = "data/uploads"

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
