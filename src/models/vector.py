from pydantic import BaseModel, Field


class VectorSearchMetadata(BaseModel):
    document_id: str
    vendor: str | None = None
    amount: float | None = None
    date: str | None = None


class VectorSearchResult(BaseModel):
    id: str
    text: str
    metadata: VectorSearchMetadata
    score: float = Field(ge=0.0)
