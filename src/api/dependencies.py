from functools import lru_cache

# pyrefly: ignore [missing-import]
from src.services.document_service import DocumentService

# pyrefly: ignore [missing-import]
from src.services.rag_service import RAGService


@lru_cache
def get_doc_service() -> DocumentService:
    return DocumentService()


@lru_cache
def get_rag_service() -> RAGService:
    return RAGService()
