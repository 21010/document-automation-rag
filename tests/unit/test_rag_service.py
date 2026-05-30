from unittest.mock import AsyncMock, MagicMock

import pytest

from src.services.rag_service import RAGService


@pytest.mark.asyncio
async def test_rag_routing_sql():
    mock_engine = MagicMock()
    mock_engine.route_and_query = AsyncMock(
        return_value={
            "route": "sql",
            "reasoning": "Query asks for total amount",
            "sql_metadata_filter": {"min_amount": 100},
        }
    )

    service = RAGService(engine=mock_engine)

    response = await service.answer("How many invoices over 100?")
    assert response["route"] == "sql"


@pytest.mark.asyncio
async def test_rag_routing_vector():
    mock_engine = MagicMock()
    mock_engine.route_and_query = AsyncMock(
        return_value={
            "route": "vector",
            "reasoning": "Semantic query",
            "sql_metadata_filter": {},
        }
    )

    service = RAGService(engine=mock_engine)

    response = await service.answer("What is an invoice?")
    assert response["route"] == "vector"
