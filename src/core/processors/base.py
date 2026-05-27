from abc import ABC, abstractmethod
from typing import Any

# pyrefly: ignore [missing-import]
from src.core.constants import DocumentType

# pyrefly: ignore [missing-import]
from src.models.invoice import StructuredInvoice


class ProcessingResult:
    def __init__(self, text: str, structured_data: StructuredInvoice, doc_type: DocumentType, raw_data: Any = None):
        self.text = text
        self.structured_data = structured_data
        self.doc_type = doc_type
        self.raw_data = raw_data


class DocumentProcessor(ABC):
    @abstractmethod
    async def process(self, file_path: str) -> ProcessingResult:
        pass
