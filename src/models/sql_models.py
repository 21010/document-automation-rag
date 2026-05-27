from datetime import UTC, datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import relationship

# pyrefly: ignore [missing-import]
from src.core.db import Base


class SQLDocument(Base):
    __tablename__ = "documents"

    id = Column(String, primary_key=True)
    filename = Column(String)
    status = Column(String)
    doc_type = Column(String)
    raw_text = Column(Text)

    # Structured fields
    nazwa_sklepu = Column(String)
    data_dokumentu = Column(String)  # Storing as string from LLM
    kwota_netto = Column(Float)
    kwota_brutto = Column(Float)
    kwota_koncowa = Column(Float)
    vat = Column(Float)
    numer_faktury = Column(String)
    sprzedawca = Column(String)
    nabywca = Column(String)

    processing_mode = Column(String)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    completed_at = Column(DateTime, nullable=True)

    items = relationship("SQLItem", back_populates="document", cascade="all, delete-orphan")


class SQLItem(Base):
    __tablename__ = "document_items"

    id = Column(String, primary_key=True)
    document_id = Column(String, ForeignKey("documents.id"))
    name = Column(String)
    quantity = Column(Float)
    unit_price = Column(Float)
    total_price = Column(Float)

    document = relationship("SQLDocument", back_populates="items")
