import os

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "RAG Invoice Processing"
    API_V1_STR: str = "/api/v1"

    # Gemini Settings
    GEMINI_API_KEY: str | None = None
    GEMINI_EMBEDDING_MODEL: str = "models/gemini-embedding-2"
    GEMINI_GENERATIVE_MODEL: str = "gemini-3.1-flash-lite"

    # Ollama Settings (Fallback)
    OPENAI_BASE_URL: str = os.getenv("OPENAI_BASE_URL", "http://localhost:11434/v1")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_GENERATIVE_MODEL: str = os.getenv("OPENAI_GENERATIVE_MODEL", "llama3.2-vision")
    OPENAI_EMBEDDING_MODEL: str = os.getenv("OPENAI_EMBEDDING_MODEL", "nomic-embed-text")

    # Database Settings
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/documents.db"

    # Vector DB Settings
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    QDRANT_IN_MEMORY: bool = True

    # Storage
    UPLOAD_DIR: str = "data/uploads"

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
