import pytest


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert "components" in response.json()


def test_upload_invalid_file(client):
    # Test with a .txt file
    files = {"file": ("test.txt", b"hello world", "text/plain")}
    response = client.post("/documents/upload", files=files)
    assert response.status_code == 400
    assert "Invalid file type" in response.json()["detail"]


def test_get_nonexistent_document(client):
    response = client.get("/documents/invalid-id")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_indexing_conflict(client):
    response = client.post("/documents/unknown-id/index")
    assert response.status_code == 404


def test_upload_valid_file(client):
    files = {"file": ("test.jpg", b"fake image content", "image/jpeg")}
    response = client.post("/documents/upload", files=files)
    assert response.status_code == 202
    data = response.json()
    assert "document_id" in data
    assert data["status"] == "queued"


def test_get_completed_document(client):
    from src.api.dependencies import get_doc_service
    from src.core.constants import DocumentStatus
    from src.main import app

    doc_service = app.dependency_overrides[get_doc_service]()
    doc_service.get_document.return_value = {
        "document_id": "123",
        "status": DocumentStatus.COMPLETED,
        "filename": "test.jpg",
        "created_at": "2023-01-01T00:00:00",
        "structured_data": {"nazwa_sklepu": "Shop"},
        "text": "hello",
        "type": "Invoice",
    }

    response = client.get("/documents/123")
    assert response.status_code == 200
    assert response.json()["status"] == DocumentStatus.COMPLETED


def test_index_document(client):
    from src.api.dependencies import get_doc_service
    from src.core.constants import DocumentStatus
    from src.main import app

    doc_service = app.dependency_overrides[get_doc_service]()
    doc_service.get_document.return_value = {
        "document_id": "123",
        "status": DocumentStatus.COMPLETED,
        "text": "hello",
        "type": "Invoice",
    }

    response = client.post("/documents/123/index")
    assert response.status_code == 200
    assert response.json()["status"] == "indexed"


def test_rag_search(client):
    from src.api.dependencies import get_rag_service
    from src.main import app

    rag_service = app.dependency_overrides[get_rag_service]()
    rag_service.search.return_value = [{"content": "chunk 1", "metadata": {"doc_type": "Invoice"}}]

    payload = {"query": "test query", "limit": 1}
    response = client.post("/rag/search", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["content"] == "chunk 1"


def test_rag_answer(client):
    from src.api.dependencies import get_rag_service
    from src.main import app

    rag_service = app.dependency_overrides[get_rag_service]()
    rag_service.answer.return_value = {
        "answer": "This is a synthesized answer.",
        "sources": [{"content": "chunk 1", "metadata": {}}],
    }

    payload = {"query": "test query"}
    response = client.post("/rag/answer", json=payload)
    assert response.status_code == 200
    assert response.json()["answer"] == "This is a synthesized answer."


def test_validation_error(client):
    # Missing required field 'query'
    payload = {"limit": 5}
    response = client.post("/rag/search", json=payload)
    assert response.status_code == 422


def test_list_documents(client):
    from src.api.dependencies import get_doc_service
    from src.core.constants import DocumentStatus
    from src.main import app

    doc_service = app.dependency_overrides[get_doc_service]()
    doc_service.list_documents.return_value = {
        "items": [
            {
                "document_id": "123",
                "status": DocumentStatus.COMPLETED,
                "text": "hello",
                "type": "Invoice",
                "structured_data": {},
                "metadata": {},
            }
        ],
        "total": 1,
    }

    response = client.get("/documents?limit=10")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert len(data["items"]) == 1


def test_update_document(client):
    from src.api.dependencies import get_doc_service
    from src.core.constants import DocumentStatus
    from src.main import app

    doc_service = app.dependency_overrides[get_doc_service]()
    doc_service.update_document.return_value = {
        "document_id": "123",
        "status": DocumentStatus.COMPLETED,
        "text": "updated text",
        "type": "Invoice",
        "structured_data": {},
        "metadata": {},
    }

    response = client.patch("/documents/123", json={"text": "updated text"})
    assert response.status_code == 200
    assert response.json()["text"] == "updated text"


def test_delete_document(client):
    from src.api.dependencies import get_doc_service
    from src.main import app

    doc_service = app.dependency_overrides[get_doc_service]()
    doc_service.delete_document.return_value = True

    response = client.delete("/documents/123")
    assert response.status_code == 204

    # Test not found
    doc_service.delete_document.return_value = False
    response = client.delete("/documents/invalid-id")
    assert response.status_code == 404


def test_batch_index_documents(client):
    from unittest.mock import AsyncMock

    from src.api.dependencies import get_doc_service, get_rag_service
    from src.main import app

    doc_service = app.dependency_overrides[get_doc_service]()
    rag_service = app.dependency_overrides[get_rag_service]()

    # Setup unindexed docs
    doc_service.get_unindexed_completed_documents.return_value = ["1", "2"]

    # Return mock docs for those ids
    async def mock_get_document(doc_id):
        return {"document_id": doc_id, "status": "completed", "text": "text for " + doc_id, "structured_data": {}}

    doc_service.get_document = AsyncMock(side_effect=mock_get_document)

    response = client.post("/documents/index:batch")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["indexed_count"] == 2
    assert rag_service.index_document.call_count == 2
