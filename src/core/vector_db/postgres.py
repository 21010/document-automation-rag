import logging

from sqlalchemy import select

from src.core.db import AsyncSessionLocal
from src.core.vector_db.base import AbstractVectorStore
from src.models.sql_models import DocumentChunk
from src.models.vector import VectorSearchMetadata, VectorSearchResult

logger = logging.getLogger(__name__)


class VectorStore(AbstractVectorStore):
    def __init__(self, vector_size: int = 768, session_factory=None):
        self.vector_size = vector_size
        self.session_factory = session_factory or AsyncSessionLocal

    async def add_documents(
        self, document_id: str, chunks: list[str], embeddings: list[list[float]], payload_base: dict
    ) -> None:
        async with self.session_factory() as session:
            for i, (chunk, emb) in enumerate(zip(chunks, embeddings)):
                chunk_id = f"{document_id}_{i}"
                doc_chunk = DocumentChunk(
                    id=chunk_id,
                    document_id=document_id,
                    text=chunk,
                    vendor=payload_base.get("vendor"),
                    amount=payload_base.get("amount"),
                    date=payload_base.get("date"),
                    embedding=emb,
                )
                session.add(doc_chunk)
            await session.commit()

    async def search(
        self, query_vector: list[float], limit: int = 5, metadata_filter: dict | None = None
    ) -> list[VectorSearchResult]:
        async with self.session_factory() as session:
            distance_expr = DocumentChunk.embedding.cosine_distance(query_vector).label("distance")
            stmt = select(DocumentChunk, distance_expr)

            if metadata_filter:
                if metadata_filter.get("vendor") is not None:
                    stmt = stmt.where(DocumentChunk.vendor == metadata_filter["vendor"])
                if metadata_filter.get("min_amount") is not None:
                    stmt = stmt.where(DocumentChunk.amount > metadata_filter["min_amount"])
                if metadata_filter.get("max_amount") is not None:
                    stmt = stmt.where(DocumentChunk.amount < metadata_filter["max_amount"])
                if metadata_filter.get("date_after") is not None:
                    stmt = stmt.where(DocumentChunk.date >= metadata_filter["date_after"])
                if metadata_filter.get("date_before") is not None:
                    stmt = stmt.where(DocumentChunk.date <= metadata_filter["date_before"])

            # Order by cosine distance
            stmt = stmt.order_by(distance_expr).limit(limit)

            result = await session.execute(stmt)
            rows = result.all()

            results = []
            for chunk, distance in rows:
                score = 1.0 - float(distance)  # Convert cosine distance to cosine similarity score
                metadata = VectorSearchMetadata(
                    document_id=chunk.document_id, vendor=chunk.vendor, amount=chunk.amount, date=chunk.date
                )
                results.append(VectorSearchResult(id=chunk.id, text=chunk.text, metadata=metadata, score=score))

            return results
