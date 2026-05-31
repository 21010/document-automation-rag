from abc import ABC, abstractmethod
from typing import Any

from src.core.constants import DocumentType


class ProcessingResult[T]:
    def __init__(self, text: str, structured_data: T, doc_type: DocumentType, raw_data: Any = None):
        self.text = text
        self.structured_data = structured_data
        self.doc_type = doc_type
        self.raw_data = raw_data


class DocumentProcessor[T](ABC):
    @abstractmethod
    async def process(self, file_path: str) -> ProcessingResult[T]:
        pass
