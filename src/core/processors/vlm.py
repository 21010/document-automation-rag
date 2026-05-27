import asyncio
import logging
import time

# pyrefly: ignore [missing-import]
from src.core.classifier import DocumentClassifier

# pyrefly: ignore [missing-import]
from src.core.constants import DocumentType

# pyrefly: ignore [missing-import]
from src.core.llm.gemini_service import GeminiService

# pyrefly: ignore [missing-import]
from src.core.processors.base import DocumentProcessor, ProcessingResult

logger = logging.getLogger(__name__)


class VLMProcessor(DocumentProcessor):
    def __init__(self):
        self.gemini = GeminiService()
        self.classifier = DocumentClassifier()

    async def process(self, file_path: str) -> ProcessingResult:
        start_total = time.time()

        # Gemini Vision Timing — run in thread pool to avoid blocking the event loop
        start_vlm = time.time()
        text, structured_data = await asyncio.to_thread(
            self.gemini.extract_from_vision, file_path, DocumentType.UNKNOWN
        )
        duration_vlm = time.time() - start_vlm
        logger.info(f"VLM Processor: Gemini Vision completed in {duration_vlm:.2f}s")

        # Classification Timing (usually instant as it uses the vision text)
        start_cls = time.time()
        doc_type = self.classifier.classify(text)
        duration_cls = time.time() - start_cls

        total_duration = time.time() - start_total
        logger.info(f"VLM Processor: Total pipeline finished in {total_duration:.2f}s")

        return ProcessingResult(
            text=text,
            structured_data=structured_data,
            doc_type=doc_type,
            raw_data={
                "vlm_duration": duration_vlm,
                "cls_duration": duration_cls,
                "total_duration": total_duration,
                "source": "Gemini Vision",
            },
        )
