from unittest.mock import AsyncMock, MagicMock

import pytest

from src.core.vector_db.postgres import VectorStore


@pytest.mark.asyncio
async def test_vector_db_insert_and_search():
    # Create mock session
    mock_session = AsyncMock()
    mock_session.add = MagicMock()

    # Mock search results for execute
    mock_row = MagicMock()
    mock_row.document_id = "test-vector-doc"
    mock_row.vendor = "fruit_vendor"
    mock_row.amount = 100
    mock_row.date = "2026-05-31"
    mock_row.id = "test-vector-doc_0"
    mock_row.text = "Apple is a fruit."

    mock_row2 = MagicMock()
    mock_row2.document_id = "test-vector-doc"
    mock_row2.vendor = "fruit_vendor"
    mock_row2.amount = 100
    mock_row2.date = "2026-05-31"
    mock_row2.id = "test-vector-doc_2"
    mock_row2.text = "Banana is yellow."

    mock_result = MagicMock()
    # Mock returning tuples (chunk, distance)
    mock_result.all.return_value = [(mock_row, 0.0), (mock_row2, 0.5)]
    mock_session.execute.return_value = mock_result

    class MockContextManager:
        async def __aenter__(self):
            return mock_session

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

    # Initialize Vector DB wrapper with our mock session factory
    vector_db = VectorStore(session_factory=lambda: MockContextManager())

    texts = ["Apple is a fruit.", "Car is a vehicle.", "Banana is yellow."]
    embeddings = [[1.0 if i == 0 else 0.0 for i in range(768)]] * 3
    payload_base = {"vendor": "fruit_vendor", "amount": 100, "date": "2026-05-31"}

    await vector_db.add_documents(
        document_id="test-vector-doc", chunks=texts, embeddings=embeddings, payload_base=payload_base
    )

    # Verify chunks were added
    assert mock_session.add.call_count == 3
    assert mock_session.commit.call_count == 1

    # Search for the closest vector
    query_embedding = [1.0 if i == 0 else 0.0 for i in range(768)]
    results = await vector_db.search(query_vector=query_embedding, limit=2)

    assert len(results) == 2
    assert results[0].text == "Apple is a fruit."
    assert results[1].text == "Banana is yellow."
    assert results[0].metadata.vendor == "fruit_vendor"
    assert results[0].metadata.amount == 100
    assert results[0].score == 1.0
    assert results[1].score == 0.5


@pytest.mark.asyncio
async def test_vector_db_metadata_filtering():
    mock_session = AsyncMock()
    mock_result = MagicMock()
    # Let's say it returns nothing to just test the query compilation
    mock_result.all.return_value = []
    mock_session.execute.return_value = mock_result

    class MockContextManager:
        async def __aenter__(self):
            return mock_session

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

    vector_db = VectorStore(session_factory=lambda: MockContextManager())

    # We call search with metadata filters
    metadata_filter = {
        "vendor": "Test Vendor",
        "min_amount": 50,
        "max_amount": 200,
        "date_after": "2026-01-01",
        "date_before": "2026-12-31",
    }

    await vector_db.search(query_vector=[0.0] * 768, limit=5, metadata_filter=metadata_filter)

    # The session.execute should have been called once
    assert mock_session.execute.call_count == 1

    # Extract the statement passed to execute
    stmt = mock_session.execute.call_args[0][0]

    # Convert statement to string to verify the WHERE clauses are present
    compiled_stmt = str(stmt.compile(compile_kwargs={"literal_binds": True}))

    # Check that our filters appear in the compiled SQL
    assert "document_chunks.vendor =" in compiled_stmt
    assert "document_chunks.amount >" in compiled_stmt
    assert "document_chunks.amount <" in compiled_stmt
    assert "document_chunks.date >=" in compiled_stmt
    assert "document_chunks.date <=" in compiled_stmt
