from typing import Protocol

from src.core.constants import DocumentType
from src.models.documents import StructuredDocument


class LLMService(Protocol):
    """Protocol defining the interface for Language Model services."""

    async def get_structured_data(self, text: str, doc_type: DocumentType = DocumentType.UNKNOWN) -> StructuredDocument:
        """Extract structured data from text using LLM."""
        ...

    async def get_embeddings(self, texts: list[str], task_type: str = "RETRIEVAL_DOCUMENT") -> list[list[float]]:
        """Get vector embeddings for a list of texts."""
        ...

    async def extract_from_vision(
        self, image_path: str, doc_type: DocumentType = DocumentType.UNKNOWN
    ) -> tuple[str, StructuredDocument]:
        """Extract raw text and structured data from an image."""
        ...

    async def route_query(self, query: str) -> dict:
        """Determine if query should use vector search or SQL filter."""
        ...

    async def generate_answer(self, query: str, context: str) -> str:
        """Generate final answer using context."""
        ...
