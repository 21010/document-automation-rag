import os
import shutil
import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile, status

from src.api.dependencies import get_doc_service, get_rag_service
from src.api.schemas import AnswerRequest, DocumentResponse, DocumentUploadResponse, SearchRequest
from src.core.config import settings
from src.core.constants import DocumentStatus
from src.services.document_service import DocumentService
from src.services.rag_service import RAGService

router = APIRouter()


async def handle_upload(background_tasks: BackgroundTasks, file: UploadFile, doc_service: DocumentService):
    filename = file.filename or ""
    if not filename.lower().endswith((".png", ".jpg", ".jpeg")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid file type. Supported: .png, .jpg, .jpeg"
        )

    document_id = str(uuid.uuid4())
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    file_path = os.path.join(settings.UPLOAD_DIR, f"{document_id}_{filename}")

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to save file: {e}")

    await doc_service.create_pending_document(document_id, filename)
    background_tasks.add_task(doc_service.process_document, document_id, file_path)

    return DocumentUploadResponse(document_id=document_id, status=DocumentStatus.QUEUED)


@router.post(
    "/documents/upload",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=DocumentUploadResponse,
    summary="Upload Document",
    description="Accepts an image file (.png, .jpg, .jpeg), assigns a unique ID, and triggers background VLM extraction.",  # noqa: E501
)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    doc_service: DocumentService = Depends(get_doc_service),
):
    return await handle_upload(background_tasks, file, doc_service)


@router.get(
    "/documents/{document_id}",
    response_model=DocumentResponse,
    summary="Check Document Status",
    description="Retrieves the processing status, structured JSON data, and extracted text for a given document.",
)
async def get_document(document_id: str, doc_service: DocumentService = Depends(get_doc_service)):
    doc = await doc_service.get_document(document_id)
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return doc


@router.post(
    "/documents/{document_id}/index",
    summary="Index Document for RAG",
    description="Chunks the extracted text of a completed document, generates embeddings, and saves them to the vector index.",  # noqa: E501
)
async def index_document(
    document_id: str,
    doc_service: DocumentService = Depends(get_doc_service),
    rag_service: RAGService = Depends(get_rag_service),
):
    doc = await doc_service.get_document(document_id)
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    if doc["status"] != DocumentStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Document is in status '{doc['status']}'. It must be 'completed' before indexing.",
        )

    if not doc.get("text"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Document has no extracted text to index."
        )

    metadata = doc.get("structured_data", {})
    rag_service.index_document(document_id, doc["text"], metadata=metadata)
    return {"status": "indexed", "document_id": document_id}


@router.post(
    "/rag/search",
    summary="Semantic Search",
    description="Searches the vector index for the most relevant document chunks matching the provided query.",
)
async def search_rag(request: SearchRequest, rag_service: RAGService = Depends(get_rag_service)):
    return rag_service.search(request.query, limit=request.limit)


@router.post(
    "/rag/answer",
    summary="RAG Question Answering",
    description="Dynamically answers user questions about indexed documents using a hybrid search and generative LLM response.",  # noqa: E501
)
async def answer_rag(request: AnswerRequest, rag_service: RAGService = Depends(get_rag_service)):
    return rag_service.answer(request.query, limit=request.limit)
