import logging

from src.core.rag.engine import RAGEngine

logger = logging.getLogger(__name__)


class RAGService:
    def __init__(self, engine: RAGEngine):
        self.engine = engine

    async def index_document(self, document_id: str, text: str, metadata: dict | None = None):
        logger.info(f"Indexing document {document_id} with semantic chunks")
        await self.engine.index_document(document_id, text, metadata=metadata)

    async def search(self, query: str, limit: int = 5):
        # Default semantic search
        results = await self.engine.search(query, limit=limit)
        return [
            {
                "document_id": r.metadata.document_id,
                "text": r.text,
                "score": r.score,
                "metadata": r.metadata.model_dump(),
            }
            for r in results
        ]

    async def answer(self, query: str, limit: int = 3):
        # Uses Hybrid Routing Optimization
        return await self.engine.route_and_query(query)
