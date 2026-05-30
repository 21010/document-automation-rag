import logging

from src.core.llm.base import LLMService

logger = logging.getLogger(__name__)

# Cache the service instance
_llm_service_instance: LLMService | None = None


def get_llm_service() -> LLMService:
    global _llm_service_instance
    if _llm_service_instance is not None:
        return _llm_service_instance

    from src.core.llm.openai_service import OpenAIService

    _llm_service_instance = OpenAIService()

    return _llm_service_instance
