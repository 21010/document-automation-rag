from datetime import datetime
from functools import lru_cache

from fastapi import APIRouter, Depends
from sqlalchemy import text

from src.core.config import settings
from src.core.db import engine
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
    description="Verifies the operational status of the API and its connection to the backend components.",
)
async def health_check(llm: LLMService = Depends(get_llm_service)):
    db_status = "error"
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"

    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "project": settings.PROJECT_NAME,
        "components": {
            "api": "ready",
            "vlm": "configured" if getattr(llm, "base_url", None) else "not_configured",
            "embedding": "configured" if getattr(llm, "embed_base_url", None) else "not_configured",
            "database": db_status,
            "rag": "ready" if getattr(llm, "embed_base_url", None) and db_status == "connected" else "not_ready",
        },
    }
