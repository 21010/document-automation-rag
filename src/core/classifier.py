from src.core.constants import DocumentType


class DocumentClassifier:
    def classify(self, text: str) -> DocumentType:
        text_lower = text.lower()

        # Heuristics for document classification
        if any(kw in text_lower for kw in ["invoice", "faktura", "nr faktury", "invoice no"]):
            return DocumentType.INVOICE

        if any(kw in text_lower for kw in ["paragon", "fiskalny", "kasa", "receipt"]):
            return DocumentType.RECEIPT

        if any(kw in text_lower for kw in ["form", "application", "formularz", "wniosek"]):
            return DocumentType.FORM

        # Fallback based on common markers
        if "total" in text_lower or "suma" in text_lower:
            return DocumentType.INVOICE

        return DocumentType.UNKNOWN
