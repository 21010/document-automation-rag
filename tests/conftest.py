import pytest
from fastapi.testclient import TestClient

from src.main import app


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    yield


@pytest.fixture
def client(monkeypatch):
    from unittest.mock import AsyncMock, MagicMock

    from src.api.dependencies import get_doc_service, get_rag_service

    # Mock init_db to prevent connecting to actual postgres
    monkeypatch.setattr("src.main.init_db", AsyncMock())

    # Create mock services
    mock_doc_service = MagicMock()
    mock_doc_service.get_document = AsyncMock(return_value=None)
    mock_doc_service.create_pending_document = AsyncMock(return_value={})
    mock_doc_service.process_document = AsyncMock(return_value=None)

    mock_rag_service = MagicMock()
    mock_rag_service.search = AsyncMock(return_value=[])
    mock_rag_service.answer = AsyncMock(return_value={"answer": "mock"})
    mock_rag_service.index_document = AsyncMock(return_value=None)

    app.dependency_overrides[get_doc_service] = lambda: mock_doc_service
    app.dependency_overrides[get_rag_service] = lambda: mock_rag_service

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()


@pytest.fixture
def mock_vlm_structured_data():
    from src.models.documents import Product, StructuredInvoice

    return StructuredInvoice(
        nazwa_sklepu="Test Shop",
        data="2026-05-16",
        kwota_koncowa=123.45,
        lista_produktow=[Product(name="Test Item", quantity=1, unit_price=123.45, total_price=123.45)],
    )
