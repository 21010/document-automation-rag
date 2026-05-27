from unittest.mock import MagicMock

# pyrefly: ignore [missing-import]
from src.services.rag_service import RAGService


def test_rag_routing_sql():
    service = RAGService()
    # Mock the engine's routing response
    service.engine.gemini.route_query = MagicMock(
        return_value={
            "route": "sql",
            "reasoning": "Query asks for total amount",
            "sql_metadata_filter": {"min_amount": 100},
        }
    )

    # Mock search result
    service.engine.search = MagicMock(return_value=[])

    response = service.answer("How many invoices over 100?")
    assert response["route"] == "sql"


def test_rag_routing_vector():
    service = RAGService()
    service.engine.gemini.route_query = MagicMock(
        return_value={"route": "vector", "reasoning": "Semantic query", "sql_metadata_filter": {}}
    )

    service.engine.search = MagicMock(return_value=[])

    response = service.answer("What is an invoice?")
    assert response["route"] == "vector"
