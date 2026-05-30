from datetime import UTC, datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import JSON, Column, DateTime, Float, ForeignKey, String, Text

from src.core.db import Base


class SQLDocument(Base):
    __tablename__ = "documents"

    id = Column(String, primary_key=True)
    filename = Column(String)
    status = Column(String)
    doc_type = Column(String)
    raw_text = Column(Text)

    structured_data = Column(JSON, nullable=True)

    processing_mode = Column(String)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    completed_at = Column(DateTime(timezone=True), nullable=True)


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(String, primary_key=True)
    document_id = Column(String, ForeignKey("documents.id", ondelete="CASCADE"), index=True)
    text = Column(Text)

    # Metadata for filtering
    vendor = Column(String, nullable=True, index=True)
    amount = Column(Float, nullable=True, index=True)
    date = Column(String, nullable=True, index=True)

    embedding = Column(Vector)
