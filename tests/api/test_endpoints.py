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
