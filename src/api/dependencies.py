from functools import lru_cache

from src.core.db import AsyncSessionLocal
from src.core.llm.factory import get_llm_service
from src.core.rag.engine import RAGEngine
from src.core.vector_db.postgres import VectorStore
from src.services.document_service import DocumentService
from src.services.rag_service import RAGService


@lru_cache
def get_doc_service() -> DocumentService:
    return DocumentService(session_factory=AsyncSessionLocal)


@lru_cache
def get_rag_service() -> RAGService:
    llm_service = get_llm_service()
    vector_store = VectorStore(vector_size=768)
    engine = RAGEngine(llm_service=llm_service, vector_store=vector_store)
    return RAGService(engine=engine)
