from src.core.constants import DocumentType


class DocumentClassifier:
    def classify(self, text: str) -> DocumentType:
        text_lower = text.lower()

        match text_lower:
            case t if any(kw in t for kw in ["invoice", "faktura", "nr faktury", "invoice no"]):
                return DocumentType.INVOICE
            case t if any(kw in t for kw in ["paragon", "fiskalny", "kasa", "receipt"]):
                return DocumentType.RECEIPT
            case t if any(kw in t for kw in ["form", "application", "formularz", "wniosek"]):
                return DocumentType.FORM
            case t if "total" in t or "suma" in t:
                return DocumentType.INVOICE
            case _:
                return DocumentType.UNKNOWN
