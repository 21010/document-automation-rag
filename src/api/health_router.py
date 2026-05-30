from datetime import datetime
from functools import lru_cache

from fastapi import APIRouter, Depends

from src.core.config import settings
from src.core.llm.base import LLMService

router = APIRouter()


@lru_cache
def get_llm_service() -> LLMService:
    """Singleton LLMService for health checks — avoids re-initializing on every poll."""
    from src.core.llm.factory import get_llm_service as factory_get_llm

    return factory_get_llm()


@router.get(
    "/health",
    summary="Health Check",
    description="Verifies the operational status of the API and its connection to the LLM backend.",
)
def health_check(llm: LLMService = Depends(get_llm_service)):
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "project": settings.PROJECT_NAME,
        "components": {
            "api": "ready",
            "llm_backend": "configured" if getattr(llm, "base_url", None) else "not_configured",
        },
    }
