import asyncio
import os

import pytest
from fastapi.testclient import TestClient

# pyrefly: ignore [missing-import]
from src.core.db import init_db

# pyrefly: ignore [missing-import]
from src.main import app


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    # Force initialize the database (this will create tables in the configured DB)
    # Since we use settings.DATABASE_URL, it might point to a local file.
    # For tests, we might want to override settings to use a test DB.
    # pyrefly: ignore [missing-import]
    from src.core.config import settings

    settings.DATABASE_URL = "sqlite+aiosqlite:///./data/test_documents.db"

    if os.path.exists("./data/test_documents.db"):
        try:
            os.remove("./data/test_documents.db")
        except OSError:
            pass

    asyncio.run(init_db())
    yield
    if os.path.exists("./data/test_documents.db"):
        pass  # Keep it for debugging or delete it
        # os.remove("./data/test_documents.db")


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def mock_gemini_structured_data():
    # pyrefly: ignore [missing-import]
    from src.models.invoice import Product, StructuredInvoice

    return StructuredInvoice(
        nazwa_sklepu="Test Shop",
        data="2026-05-16",
        kwota_koncowa=123.45,
        lista_produktow=[Product(name="Test Item", quantity=1, unit_price=123.45, total_price=123.45)],
    )
