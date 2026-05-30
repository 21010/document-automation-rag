from unittest.mock import MagicMock

from src.core.rag.engine import RAGEngine


def test_semantic_chunking_with_metadata():
    engine = RAGEngine(llm_service=MagicMock(), vector_store=MagicMock())
    metadata = {
        "nazwa_sklepu": "Lidl",
        "kwota_koncowa": 50.0,
        "lista_produktow": [{"name": "Milk", "total_price": 5.0}],
    }
    chunks = engine.chunk_text_semantically("Full raw text...", structured_data=metadata)

    assert len(chunks) >= 3
    assert "Lidl" in chunks[0]
    assert "50.0" in chunks[0]  # Totals are now in the metadata header chunk
    assert "Milk" in chunks[1]


def test_fallback_chunking():
    engine = RAGEngine(llm_service=MagicMock(), vector_store=MagicMock())
    # No metadata
    chunks = engine.chunk_text_semantically("A" * 2000)
    assert len(chunks) >= 2
