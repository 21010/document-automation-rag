from enum import StrEnum


class DocumentStatus(StrEnum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class DocumentType(StrEnum):
    INVOICE = "Invoice"
    RECEIPT = "Receipt"
    FORM = "Form"
    UNKNOWN = "Unknown"
