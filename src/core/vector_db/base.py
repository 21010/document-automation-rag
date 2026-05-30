from abc import ABC, abstractmethod

from src.models.vector import VectorSearchResult


class AbstractVectorStore(ABC):
    @abstractmethod
    async def add_documents(
        self, document_id: str, chunks: list[str], embeddings: list[list[float]], payload_base: dict
    ) -> None:
        pass

    @abstractmethod
    async def search(
        self, query_vector: list[float], limit: int = 5, metadata_filter: dict | None = None
    ) -> list[VectorSearchResult]:
        pass
