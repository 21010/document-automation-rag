from qdrant_client import QdrantClient
from qdrant_client.http import models

# pyrefly: ignore [missing-import]
from src.core.config import settings


class VectorStore:
    def __init__(self, vector_size: int = 768):
        if settings.QDRANT_IN_MEMORY:
            self.client = QdrantClient(":memory:")
        else:
            self.client = QdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT)

        self.collection_name = "documents"
        self.vector_size = vector_size
        self._ensure_collection()

    def _ensure_collection(self):
        try:
            if not self.client.collection_exists(self.collection_name):
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=models.VectorParams(size=self.vector_size, distance=models.Distance.COSINE),
                )
        except Exception:
            self.client.recreate_collection(
                collection_name=self.collection_name,
                vectors_config=models.VectorParams(size=self.vector_size, distance=models.Distance.COSINE),
            )

    def add_documents(self, document_id: str, chunks: list[str], embeddings: list[list[float]]):
        points = [
            models.PointStruct(id=f"{document_id}_{i}", vector=emb, payload={"document_id": document_id, "text": chunk})
            for i, (chunk, emb) in enumerate(zip(chunks, embeddings))
        ]
        self.client.upsert(collection_name=self.collection_name, points=points)

    def search(self, query_vector: list[float], limit: int = 5):
        # pyrefly: ignore [missing-attribute]
        return self.client.query_points(collection_name=self.collection_name, query=query_vector, limit=limit).points
