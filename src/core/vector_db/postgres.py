import logging

from sqlalchemy import select

from src.core.db import AsyncSessionLocal
from src.core.vector_db.base import AbstractVectorStore
from src.models.sql_models import DocumentChunk
from src.models.vector import VectorSearchMetadata, VectorSearchResult

logger = logging.getLogger(__name__)


class VectorStore(AbstractVectorStore):
    def __init__(self, vector_size: int = 768):
        self.vector_size = vector_size

    async def add_documents(
        self, document_id: str, chunks: list[str], embeddings: list[list[float]], payload_base: dict
    ) -> None:
        async with AsyncSessionLocal() as session:
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
        async with AsyncSessionLocal() as session:
            distance_expr = DocumentChunk.embedding.cosine_distance(query_vector).label("distance")
            stmt = select(DocumentChunk, distance_expr)

            if metadata_filter:
                if metadata_filter.get("vendor"):
                    stmt = stmt.where(DocumentChunk.vendor == metadata_filter["vendor"])
                if metadata_filter.get("min_amount"):
                    stmt = stmt.where(DocumentChunk.amount > metadata_filter["min_amount"])

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
