import logging

from src.core.vector_db.base import AbstractVectorStore

logger = logging.getLogger(__name__)


class RAGEngine:
    def __init__(self, llm_service, vector_store: AbstractVectorStore):
        self.llm = llm_service
        self.vector_store = vector_store

    async def get_embeddings(self, texts: list[str]) -> list[list[float]]:
        return await self.llm.get_embeddings(texts)

    def chunk_text_semantically(self, text: str, structured_data: dict | None = None) -> list[str]:
        if not structured_data:
            return [text[i : i + 1000] for i in range(0, len(text), 900)]

        chunks = []
        # Dynamic extraction for Document Ref (could be Invoice Number, Date, etc.)
        doc_ref_val = structured_data.get("numer_faktury") or structured_data.get("data") or "Brak numeru"
        doc_ref = f"Dokument: {doc_ref_val}"

        # Create dynamic header for all primary string/float fields
        header_lines = [f"[{doc_ref}]", "Metadane Dokumentu (Metadata):"]
        for key, value in structured_data.items():
            if value is not None and not isinstance(value, list):
                # Clean up the key to be more readable
                clean_key = key.replace('_', ' ').capitalize()
                header_lines.append(f"{clean_key}: {value}")
        chunks.append("\n".join(header_lines))

        # Handle lists like products or form fields dynamically
        items = structured_data.get("lista_produktow", [])
        if items:
            item_text = f"[{doc_ref}]\nLista produktów (Items purchased):\n" + "\n".join(
                [f"- {i.get('name')}: {i.get('total_price') or i.get('unit_price') or ''}" for i in items]
            )
            chunks.append(item_text)
            
        form_fields = structured_data.get("pola_formularza", [])
        if form_fields:
            form_text = f"[{doc_ref}]\nPola formularza (Form Fields):\n" + "\n".join(
                [f"- {f.get('question')}: {f.get('answer')}" for f in form_fields]
            )
            chunks.append(form_text)

        chunks.append(f"[{doc_ref}]\nPełny tekst dokumentu (Raw text):\n" + text[:2000])

        return chunks

    async def index_document(self, document_id: str, text: str, metadata: dict | None = None):
        chunks = self.chunk_text_semantically(text, structured_data=metadata)
        if not chunks:
            return

        embeddings = await self.get_embeddings(chunks)

        payload_base = {
            "document_id": document_id,
            "vendor": metadata.get("nazwa_sklepu") if metadata else None,
            "amount": metadata.get("kwota_koncowa") if metadata else None,
            "date": metadata.get("data") if metadata else None,
        }

        await self.vector_store.add_documents(document_id, chunks, embeddings, payload_base)

    async def search(self, query: str, limit: int = 5, metadata_filter: dict | None = None):
        query_embedding = (await self.llm.get_embeddings([query], task_type="RETRIEVAL_QUERY"))[0]
        return await self.vector_store.search(query_embedding, limit=limit, metadata_filter=metadata_filter)

    async def route_and_query(self, query: str):
        routing_info = await self.llm.route_query(query)
        route_type = routing_info.get("route", "vector")
        logger.info(f"Query routed to: {route_type}")

        if route_type == "sql":
            results = await self.search(query, metadata_filter=routing_info.get("sql_metadata_filter"))
        else:
            results = await self.search(query)

        if not results:
            return {"answer": "I couldn't find relevant information.", "sources": [], "route": route_type}

        context = "\n---\n".join([r.text for r in results])
        answer = await self.llm.generate_answer(query, context)

        return {
            "answer": answer,
            "sources": list(set([r.metadata.document_id for r in results])),
            "route": route_type,
            "reasoning": routing_info.get("reasoning", "Default routing applied."),
        }
