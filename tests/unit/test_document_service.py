from unittest.mock import AsyncMock, MagicMock

import pytest

from src.core.constants import DocumentStatus
from src.services.document_service import DocumentService


@pytest.mark.asyncio
async def test_list_documents():
    mock_session = AsyncMock()

    mock_row1 = MagicMock()
    mock_row1.id = "1"
    mock_row1.status = DocumentStatus.COMPLETED
    mock_row1.raw_text = "doc 1"
    mock_row1.doc_type = "Invoice"
    mock_row1.structured_data = {}
    mock_row1.filename = "test1.jpg"
    mock_row1.processing_mode = "vlm"
    mock_row1.created_at = None
    mock_row1.completed_at = None

    mock_row2 = MagicMock()
    mock_row2.id = "2"
    mock_row2.status = DocumentStatus.QUEUED
    mock_row2.raw_text = None
    mock_row2.doc_type = None
    mock_row2.structured_data = None
    mock_row2.filename = "test2.jpg"
    mock_row2.processing_mode = None
    mock_row2.created_at = None
    mock_row2.completed_at = None

    mock_result = MagicMock()
    mock_result.scalars().all.return_value = [mock_row1, mock_row2]
    mock_session.execute.return_value = mock_result

    mock_session.scalar.return_value = 2  # Total count

    mock_session_factory = MagicMock()
    mock_session_factory.return_value.__aenter__.return_value = mock_session

    service = DocumentService(session_factory=mock_session_factory)

    res = await service.list_documents(status=DocumentStatus.COMPLETED, doc_type="Invoice")

    assert res["total"] == 2
    assert len(res["items"]) == 2
    assert res["items"][0]["document_id"] == "1"

    # Verify execute and scalar were called
    assert mock_session.execute.call_count == 1
    assert mock_session.scalar.call_count == 1


@pytest.mark.asyncio
async def test_delete_document():
    mock_session = AsyncMock()

    mock_doc = MagicMock()
    mock_session.get.return_value = mock_doc

    mock_session_factory = MagicMock()
    mock_session_factory.return_value.__aenter__.return_value = mock_session

    service = DocumentService(session_factory=mock_session_factory)

    # Test found
    res = await service.delete_document("1")
    assert res is True
    assert mock_session.delete.call_count == 1
    assert mock_session.commit.call_count == 1

    # Test not found
    mock_session.get.return_value = None
    res = await service.delete_document("2")
    assert res is False
    assert mock_session.delete.call_count == 1  # Hasn't increased


@pytest.mark.asyncio
async def test_update_document():
    mock_session = AsyncMock()

    mock_doc = MagicMock()
    mock_doc.raw_text = "old"
    mock_doc.structured_data = {}
    mock_doc.status = DocumentStatus.QUEUED
    # For get_document return mapping
    mock_doc.id = "1"
    mock_doc.doc_type = "Invoice"
    mock_doc.filename = "test.jpg"
    mock_doc.processing_mode = "vlm"
    mock_doc.created_at = None
    mock_doc.completed_at = None

    mock_session.get.return_value = mock_doc

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_doc
    mock_session.execute.return_value = mock_result

    mock_session_factory = MagicMock()
    mock_session_factory.return_value.__aenter__.return_value = mock_session

    service = DocumentService(session_factory=mock_session_factory)

    res = await service.update_document("1", {"text": "new", "status": DocumentStatus.COMPLETED})

    assert mock_doc.raw_text == "new"
    assert mock_doc.status == DocumentStatus.COMPLETED
    assert mock_session.commit.call_count == 1

    assert res is not None
    assert res["text"] == "new"


@pytest.mark.asyncio
async def test_get_unindexed_completed_documents():
    mock_session = AsyncMock()

    mock_result = MagicMock()
    mock_result.scalars().all.return_value = ["doc1", "doc2"]
    mock_session.execute.return_value = mock_result

    mock_session_factory = MagicMock()
    mock_session_factory.return_value.__aenter__.return_value = mock_session

    service = DocumentService(session_factory=mock_session_factory)

    res = await service.get_unindexed_completed_documents()
    assert res == ["doc1", "doc2"]
    assert mock_session.execute.call_count == 1
