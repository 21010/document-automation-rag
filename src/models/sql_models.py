from datetime import UTC, datetime

from sqlalchemy import Column, DateTime, String, Text, JSON
from src.core.db import Base

class SQLDocument(Base):
    __tablename__ = "documents"

    id = Column(String, primary_key=True)
    filename = Column(String)
    status = Column(String)
    doc_type = Column(String)
    raw_text = Column(Text)

    # Polymorphic structured data
    structured_data = Column(JSON, nullable=True)

    processing_mode = Column(String)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    completed_at = Column(DateTime, nullable=True)
