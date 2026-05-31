import logging
import time

from src.core.classifier import DocumentClassifier
from src.core.constants import DocumentType
from src.core.llm.factory import get_llm_service
from src.core.processors.base import DocumentProcessor, ProcessingResult
from src.models.documents import StructuredDocument

logger = logging.getLogger(__name__)


class VLMProcessor(DocumentProcessor[StructuredDocument]):
    def __init__(self):
        self.llm = get_llm_service()
        self.classifier = DocumentClassifier()

    async def process(self, file_path: str) -> ProcessingResult[StructuredDocument]:
        start_total = time.time()

        # VLM Timing
        start_vlm = time.time()
        text, structured_data, usage = await self.llm.extract_from_vision(file_path, DocumentType.UNKNOWN)
        duration_vlm = time.time() - start_vlm
        logger.info(
            f"VLM Processor: Extraction completed in {duration_vlm:.2f}s, tokens used: {usage.get('total_tokens', 0)}"
        )

        # Classification Timing
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
                "usage": usage,
                "source": "OpenAI VLM",
            },
        )
