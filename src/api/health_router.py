from datetime import datetime
from functools import lru_cache

from fastapi import APIRouter, Depends

# pyrefly: ignore [missing-import]
from src.core.config import settings

# pyrefly: ignore [missing-import]
from src.core.llm.gemini_service import GeminiService

router = APIRouter()


@lru_cache
def get_gemini_service() -> GeminiService:
    """Singleton GeminiService for health checks — avoids re-initializing on every poll."""
    return GeminiService()


@router.get(
    "/health",
    summary="Health Check",
    description="Verifies the operational status of the API and its connection to the Gemini SDK.",
)
def health_check(gemini: GeminiService = Depends(get_gemini_service)):
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "project": settings.PROJECT_NAME,
        "components": {
            "api": "ready",
            "gemini_sdk": "ready" if gemini.client is not None else "not_configured",
        },
    }
