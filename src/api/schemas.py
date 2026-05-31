from pydantic import BaseModel

from src.core.constants import DocumentStatus, DocumentType


class DocumentUploadResponse(BaseModel):
    document_id: str
    status: DocumentStatus


class DocumentResponse(BaseModel):
    document_id: str
    status: DocumentStatus
    text: str | None = None
    type: DocumentType | None = None
    structured_data: dict | None = None
    error: str | None = None
    metadata: dict | None = None  # filename, processing_mode, created_at, completed_at


class SearchRequest(BaseModel):
    query: str
    limit: int = 5


class AnswerRequest(BaseModel):
    query: str
    limit: int = 3


class DocumentListResponse(BaseModel):
    items: list[DocumentResponse]
    total: int


class DocumentUpdateRequest(BaseModel):
    text: str | None = None
    structured_data: dict | None = None
    status: DocumentStatus | None = None
