import logging
import uuid

# pyrefly: ignore [missing-import]
from src.core.llm.gemini_service import GeminiService

# pyrefly: ignore [missing-import]
from src.core.vector_db.qdrant import VectorStore

logger = logging.getLogger(__name__)


class RAGEngine:
    def __init__(self):
        self.gemini = GeminiService()
        self.vector_store = None

    def _init_vector_store(self, embedding_example: list[float]):
        if self.vector_store is None:
            dimension = len(embedding_example)
            self.vector_store = VectorStore(vector_size=dimension)

    def get_embeddings(self, texts: list[str]) -> list[list[float]]:
        return self.gemini.get_embeddings(texts)

    def chunk_text_semantically(self, text: str, structured_data: dict | None = None) -> list[str]:
        """
        Optimization 2: Semantic Chunking.
        Uses structured data to create logical chunks (e.g., vendor info, items, totals).
        """
        if not structured_data:
            # Fallback to character chunking
            return [text[i : i + 1000] for i in range(0, len(text), 900)]

        chunks = []
        doc_ref = f"Faktura/Dokument: {structured_data.get('numer_faktury', 'Brak numeru')}"

        # Chunk 1: Header/Vendor
        header = (
            f"[{doc_ref}]\n"
            f"Sprzedawca (Sklep/Vendor): {structured_data.get('nazwa_sklepu')}\n"
            f"Nabywca (Buyer): {structured_data.get('nabywca')}\n"
            f"Data: {structured_data.get('data')}\n"
            f"Numer faktury: {structured_data.get('numer_faktury')}"
        )
        chunks.append(header)

        # Chunk 2+: Items (grouping them to avoid too many small chunks)
        items = structured_data.get("lista_produktow", [])
        if items:
            item_text = f"[{doc_ref}]\nLista produktów (Items purchased):\n" + "\n".join(
                [f"- {i.get('name')}: {i.get('total_price')}" for i in items]
            )
            chunks.append(item_text)

        # Chunk Last: Totals/Tax
        totals = (
            f"[{doc_ref}]\nPodsumowanie (Totals):\n"
            f"Kwota netto: {structured_data.get('kwota_netto')}\n"
            f"Kwota brutto: {structured_data.get('kwota_brutto')}\n"
            f"VAT: {structured_data.get('VAT')}\n"
            f"Kwota końcowa (Total): {structured_data.get('kwota_koncowa')}"
        )
        chunks.append(totals)

        # Include full raw text as a safety fallback chunk
        chunks.append(f"[{doc_ref}]\nPełny tekst dokumentu (Raw text):\n" + text[:2000])

        return chunks

    def index_document(self, document_id: str, text: str, metadata: dict | None = None):
        """
        Optimization 3: Metadata-Aware Indexing.
        """
        chunks = self.chunk_text_semantically(text, structured_data=metadata)
        if not chunks:
            return

        embeddings = self.get_embeddings(chunks)
        self._init_vector_store(embeddings[0])
        assert self.vector_store is not None, "Vector store initialization failed"

        # Payload Alignment: Adding metadata to every point
        payload_base = {
            "document_id": document_id,
            "vendor": metadata.get("nazwa_sklepu") if metadata else None,
            "amount": metadata.get("kwota_koncowa") if metadata else None,
            "date": metadata.get("data") if metadata else None,
        }

        points = []
        from qdrant_client.http import models

        for i, (chunk, emb) in enumerate(zip(chunks, embeddings)):
            payload = payload_base.copy()
            payload["text"] = chunk
            # Qdrant requires integer or UUID-format string IDs.
            # uuid5 is deterministic: same document+index always maps to same UUID (idempotent upserts).
            point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{document_id}_{i}"))
            points.append(models.PointStruct(id=point_id, vector=emb, payload=payload))

        self.vector_store.client.upsert(collection_name=self.vector_store.collection_name, points=points)

    def search(self, query: str, limit: int = 5, metadata_filter: dict | None = None):
        # Use RETRIEVAL_QUERY task type for query embeddings (vs RETRIEVAL_DOCUMENT for indexing)
        # This asymmetric task typing improves cosine similarity accuracy.
        query_embedding = self.gemini.get_embeddings([query], task_type="RETRIEVAL_QUERY")[0]
        self._init_vector_store(query_embedding)
        assert self.vector_store is not None, "Vector store initialization failed"

        # Pre-filtering optimization
        from qdrant_client.http import models

        filter_conditions = []
        if metadata_filter:
            if metadata_filter.get("vendor"):
                filter_conditions.append(
                    models.FieldCondition(key="vendor", match=models.MatchValue(value=metadata_filter["vendor"]))
                )
            if metadata_filter.get("min_amount"):
                filter_conditions.append(
                    models.FieldCondition(key="amount", range=models.Range(gt=metadata_filter["min_amount"]))
                )

        qdrant_filter = models.Filter(must=filter_conditions) if filter_conditions else None

        return self.vector_store.client.query_points(
            collection_name=self.vector_store.collection_name,
            query=query_embedding,
            query_filter=qdrant_filter,
            limit=limit,
        ).points

    def route_and_query(self, query: str):
        """
        Optimization 1: Hybrid Query Routing.
        """
        routing_info = self.gemini.route_query(query)
        route_type = routing_info.get("route", "vector")
        logger.info(f"Query routed to: {route_type}")

        if route_type == "sql":
            # For this demo, we'll still use vector search but with tight SQL filters
            results = self.search(query, metadata_filter=routing_info.get("sql_metadata_filter"))
        else:
            results = self.search(query)

        if not results:
            return {"answer": "I couldn't find relevant information.", "sources": [], "route": route_type}

        context = "\n---\n".join([r.payload["text"] for r in results])
        answer = self.gemini.generate_answer(query, context)

        return {
            "answer": answer,
            "sources": list(set([r.payload["document_id"] for r in results])),
            "route": route_type,
            "reasoning": routing_info.get("reasoning", "Default routing applied."),
        }
