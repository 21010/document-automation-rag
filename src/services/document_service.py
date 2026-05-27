import logging
import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.core.constants import DocumentStatus
from src.core.db import AsyncSessionLocal
from src.core.processors.vlm import VLMProcessor
from src.models.sql_models import SQLDocument, SQLItem

logger = logging.getLogger(__name__)


class DocumentService:
    def __init__(self):
        self.vlm_processor = VLMProcessor()

    async def process_document(self, document_id: str, file_path: str):
        async with AsyncSessionLocal() as session:
            doc = await session.get(SQLDocument, document_id)
            if doc:
                doc.status = DocumentStatus.PROCESSING
                doc.processing_mode = "vlm"
                await session.commit()

            try:
                result = await self.vlm_processor.process(file_path)

                doc = await session.get(SQLDocument, document_id)
                doc.status = DocumentStatus.COMPLETED
                doc.raw_text = result.text
                doc.doc_type = result.doc_type
                doc.completed_at = datetime.now(UTC)

                s = result.structured_data
                doc.nazwa_sklepu = s.nazwa_sklepu
                doc.data_dokumentu = s.data
                doc.kwota_netto = s.kwota_netto
                doc.kwota_brutto = s.kwota_brutto
                doc.kwota_koncowa = s.kwota_koncowa
                doc.vat = s.VAT
                doc.numer_faktury = s.numer_faktury
                doc.sprzedawca = s.sprzedawca
                doc.nabywca = s.nabywca

                for item in s.lista_produktow:
                    sql_item = SQLItem(
                        id=str(uuid.uuid4()),
                        document_id=document_id,
                        name=item.name,
                        quantity=item.quantity,
                        unit_price=item.unit_price,
                        total_price=item.total_price,
                    )
                    session.add(sql_item)

                await session.commit()
                logger.info(f"Successfully processed {document_id} using VLM mode")
            except Exception as e:
                logger.error(f"Error processing {document_id} in VLM mode: {e}")
                doc = await session.get(SQLDocument, document_id)
                if doc:
                    doc.status = DocumentStatus.FAILED
                    await session.commit()

    async def create_pending_document(self, document_id: str, filename: str) -> dict:
        async with AsyncSessionLocal() as session:
            doc = SQLDocument(id=document_id, filename=filename, status=DocumentStatus.QUEUED)
            session.add(doc)
            await session.commit()
            return {"document_id": document_id, "status": DocumentStatus.QUEUED}

    async def get_document(self, document_id: str) -> dict | None:
        async with AsyncSessionLocal() as session:
            # Use selectinload to fetch items eagerly
            stmt = select(SQLDocument).options(selectinload(SQLDocument.items)).where(SQLDocument.id == document_id)
            result = await session.execute(stmt)
            doc = result.scalar_one_or_none()
            if not doc:
                return None

            return {
                "document_id": doc.id,
                "status": doc.status,
                "text": doc.raw_text,
                "type": doc.doc_type,
                "structured_data": {
                    "nazwa_sklepu": doc.nazwa_sklepu,
                    "data": doc.data_dokumentu,
                    "kwota_koncowa": doc.kwota_koncowa,
                    "kwota_netto": doc.kwota_netto,
                    "kwota_brutto": doc.kwota_brutto,
                    "VAT": doc.vat,
                    "numer_faktury": doc.numer_faktury,
                    "sprzedawca": doc.sprzedawca,
                    "nabywca": doc.nabywca,
                    "lista_produktow": [
                        {
                            "name": item.name,
                            "quantity": item.quantity,
                            "unit_price": item.unit_price,
                            "total_price": item.total_price,
                        }
                        for item in doc.items
                    ],
                },
                "metadata": {
                    "filename": doc.filename,
                    "processing_mode": doc.processing_mode,
                    "created_at": doc.created_at.isoformat() if doc.created_at else None,
                    "completed_at": doc.completed_at.isoformat() if doc.completed_at else None,
                },
            }
