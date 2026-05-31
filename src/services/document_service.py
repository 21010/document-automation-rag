import logging
from datetime import UTC, datetime

from sqlalchemy import select

from src.core.constants import DocumentStatus
from src.core.processors.vlm import VLMProcessor
from src.models.sql_models import SQLDocument

logger = logging.getLogger(__name__)


class DocumentService:
    def __init__(self, session_factory):
        self.session_factory = session_factory
        self.vlm_processor = VLMProcessor()

    async def process_document(self, document_id: str, file_path: str):
        async with self.session_factory() as session:
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
                doc.structured_data = s.model_dump()

                await session.commit()
                logger.info(f"Successfully processed {document_id} using VLM mode")
            except Exception as e:
                logger.error(f"Error processing {document_id} in VLM mode: {e}")
                doc = await session.get(SQLDocument, document_id)
                if doc:
                    doc.status = DocumentStatus.FAILED
                    await session.commit()

    async def create_pending_document(self, document_id: str, filename: str, file_hash: str | None = None) -> dict:
        async with self.session_factory() as session:
            doc = SQLDocument(id=document_id, filename=filename, file_hash=file_hash, status=DocumentStatus.QUEUED)
            session.add(doc)
            await session.commit()
            return {"document_id": document_id, "status": DocumentStatus.QUEUED}

    async def get_document_by_hash(self, file_hash: str) -> str | None:
        async with self.session_factory() as session:
            stmt = select(SQLDocument.id).where(SQLDocument.file_hash == file_hash)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def get_document(self, document_id: str) -> dict | None:
        async with self.session_factory() as session:
            stmt = select(SQLDocument).where(SQLDocument.id == document_id)
            result = await session.execute(stmt)
            doc = result.scalar_one_or_none()
            if not doc:
                return None

            return {
                "document_id": doc.id,
                "status": doc.status,
                "text": doc.raw_text,
                "type": doc.doc_type,
                "structured_data": doc.structured_data,
                "metadata": {
                    "filename": doc.filename,
                    "processing_mode": doc.processing_mode,
                    "created_at": doc.created_at.isoformat() if doc.created_at else None,
                    "completed_at": doc.completed_at.isoformat() if doc.completed_at else None,
                },
            }

    async def list_documents(
        self,
        skip: int = 0,
        limit: int = 50,
        status: DocumentStatus | None = None,
        doc_type: str | None = None,
    ) -> dict:
        from sqlalchemy import func

        async with self.session_factory() as session:
            stmt = select(SQLDocument).order_by(SQLDocument.created_at.desc())
            if status:
                stmt = stmt.where(SQLDocument.status == status)
            if doc_type:
                stmt = stmt.where(SQLDocument.doc_type == doc_type)

            stmt = stmt.offset(skip).limit(limit)
            result = await session.execute(stmt)
            docs = result.scalars().all()

            count_stmt = select(func.count(SQLDocument.id))
            if status:
                count_stmt = count_stmt.where(SQLDocument.status == status)
            if doc_type:
                count_stmt = count_stmt.where(SQLDocument.doc_type == doc_type)

            total = await session.scalar(count_stmt)

            return {
                "items": [
                    {
                        "document_id": d.id,
                        "status": d.status,
                        "text": d.raw_text,
                        "type": d.doc_type,
                        "structured_data": d.structured_data,
                        "metadata": {
                            "filename": d.filename,
                            "processing_mode": d.processing_mode,
                            "created_at": d.created_at.isoformat() if d.created_at else None,
                            "completed_at": d.completed_at.isoformat() if d.completed_at else None,
                        },
                    }
                    for d in docs
                ],
                "total": total or 0,
            }

    async def delete_document(self, document_id: str) -> bool:
        async with self.session_factory() as session:
            doc = await session.get(SQLDocument, document_id)
            if not doc:
                return False
            await session.delete(doc)
            await session.commit()
            return True

    async def update_document(self, document_id: str, updates: dict) -> dict | None:
        async with self.session_factory() as session:
            doc = await session.get(SQLDocument, document_id)
            if not doc:
                return None

            if "text" in updates and updates["text"] is not None:
                doc.raw_text = updates["text"]
            if "structured_data" in updates and updates["structured_data"] is not None:
                doc.structured_data = updates["structured_data"]
            if "status" in updates and updates["status"] is not None:
                doc.status = updates["status"]

            await session.commit()
            return await self.get_document(document_id)

    async def get_unindexed_completed_documents(self) -> list[str]:
        from src.models.sql_models import DocumentChunk

        async with self.session_factory() as session:
            subq = select(DocumentChunk.document_id).distinct()
            stmt = select(SQLDocument.id).where(
                SQLDocument.status == DocumentStatus.COMPLETED, SQLDocument.id.not_in(subq)
            )
            result = await session.execute(stmt)
            return list(result.scalars().all())
