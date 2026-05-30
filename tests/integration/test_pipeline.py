from unittest.mock import AsyncMock, MagicMock

import pytest

from src.core.constants import DocumentStatus
from src.services.document_service import DocumentService


@pytest.mark.asyncio
async def test_full_pipeline_flow(mock_vlm_structured_data):
    mock_doc = MagicMock()
    mock_doc.status = DocumentStatus.COMPLETED
    mock_doc.raw_text = "Invoice text"
    mock_doc.doc_type = "Invoice"
    mock_doc.structured_data = {"nazwa_sklepu": "Test Shop"}
    mock_doc.filename = "test.jpg"
    mock_doc.processing_mode = "vlm"
    mock_doc.created_at = None
    mock_doc.completed_at = None

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_doc

    mock_session = AsyncMock()
    mock_session.get.return_value = mock_doc
    mock_session.execute.return_value = mock_result
    mock_session.add = MagicMock()
    mock_session.__aenter__.return_value = mock_session
    mock_session_factory = MagicMock(return_value=mock_session)

    service = DocumentService(session_factory=mock_session_factory)

    # Mock the processors
    service.vlm_processor.llm.extract_from_vision = AsyncMock(return_value=("Invoice text", mock_vlm_structured_data))

    import uuid

    doc_id = f"test-doc-{uuid.uuid4()}"
    await service.create_pending_document(doc_id, "test.jpg")

    # Process
    await service.process_document(doc_id, "dummy_path")

    # Verify result
    doc = await service.get_document(doc_id)
    assert doc is not None
    assert doc["status"] == DocumentStatus.COMPLETED
    assert doc["structured_data"]["nazwa_sklepu"] == "Test Shop"
    assert doc["type"] == "Invoice"
