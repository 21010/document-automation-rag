from fastapi.testclient import TestClient

# pyrefly: ignore [missing-import]
from src.main import app

client = TestClient(app)


def test_health():
    response = client.get("/api/v1/health")  # Wait, I didn't add prefix in routes.py yet.
    # Checking src/api/routes.py, I used @router.get("/health")
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
