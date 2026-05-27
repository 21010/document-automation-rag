import pytest
from fastapi.testclient import TestClient

# pyrefly: ignore [missing-import]
from src.main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert "components" in response.json()


def test_upload_invalid_file():
    # Test with a .txt file
    files = {"file": ("test.txt", b"hello world", "text/plain")}
    response = client.post("/documents/upload", files=files)
    assert response.status_code == 400
    assert "Invalid file type" in response.json()["detail"]


def test_get_nonexistent_document():
    response = client.get("/documents/invalid-id")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_indexing_conflict():
    # In a real test, we would mock the DB to have a 'queued' document
    # For now, we just test the 404 for an unknown doc
    response = client.post("/documents/unknown-id/index")
    assert response.status_code == 404
