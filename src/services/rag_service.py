import logging

# pyrefly: ignore [missing-import]
from src.core.rag.engine import RAGEngine

logger = logging.getLogger(__name__)


class RAGService:
    def __init__(self):
        self.engine = RAGEngine()

    def index_document(self, document_id: str, text: str, metadata: dict | None = None):
        logger.info(f"Indexing document {document_id} with semantic chunks")
        self.engine.index_document(document_id, text, metadata=metadata)

    def search(self, query: str, limit: int = 5):
        # Default semantic search
        results = self.engine.search(query, limit=limit)
        return [
            {
                "document_id": r.payload["document_id"],
                "text": r.payload["text"],
                "score": r.score,
                "metadata": r.payload,
            }
            for r in results
        ]

    def answer(self, query: str, limit: int = 3):
        # Uses Hybrid Routing Optimization
        return self.engine.route_and_query(query)
