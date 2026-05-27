from unittest.mock import MagicMock

import pytest

from src.core.constants import DocumentStatus
from src.services.document_service import DocumentService


@pytest.mark.asyncio
async def test_full_pipeline_flow(mock_gemini_structured_data):
    # Setup service with mocks
    service = DocumentService()

    # Mock the processors
    service.vlm_processor.gemini.extract_from_vision = MagicMock(
        return_value=("Invoice text", mock_gemini_structured_data)
    )

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
