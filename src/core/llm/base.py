from typing import Protocol

# pyrefly: ignore [missing-import]
from src.core.constants import DocumentType

# pyrefly: ignore [missing-import]
from src.models.invoice import StructuredInvoice


class LLMService(Protocol):
    """Protocol defining the interface for Language Model services."""

    def get_structured_data(self, text: str, doc_type: DocumentType = DocumentType.UNKNOWN) -> StructuredInvoice:
        """Extract structured data from text using LLM."""
        ...

    def get_embeddings(self, texts: list[str], task_type: str = "RETRIEVAL_DOCUMENT") -> list[list[float]]:
        """Get vector embeddings for a list of texts."""
        ...

    def extract_from_vision(
        self, image_path: str, doc_type: DocumentType = DocumentType.UNKNOWN
    ) -> tuple[str, StructuredInvoice]:
        """Extract raw text and structured data from an image."""
        ...

    def route_query(self, query: str) -> dict:
        """Determine if query should use vector search or SQL filter."""
        ...

    def generate_answer(self, query: str, context: str) -> str:
        """Generate final answer using context."""
        ...
