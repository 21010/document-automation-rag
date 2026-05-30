# pyrefly: ignore [missing-import]
from src.core.constants import DocumentType

DEFAULT_EXTRACTION_PROMPT = """
Extract structured information from the following document text. 
Return ONLY a valid JSON object exactly matching this strict JSON schema definition:
{schema_json}
"""

INVOICE_PROMPT = """
You are an expert accountant. Analyze this INVOICE. 
Pay special attention to TAX details (VAT), NIP numbers, and the distinction between Seller (Sprzedawca)
and Buyer (Nabywca).
Extract structured information matching the standard schema.
"""

RECEIPT_PROMPT = """
Analyze this retail RECEIPT/PARAGON. 
Focus on the Store Name, the list of items purchased, and the final total amount. 
Retail receipts often have abbreviated item names; try to keep them recognizable.
"""

FORM_PROMPT = """
Analyze this FORM. 
Extract the primary entity names, dates, and any numerical values found in the fields.
If specific line items aren't present, use the 'lista_produktow' to store key field-value pairs if applicable.
"""


def get_prompt_for_type(doc_type: DocumentType, schema_json: str) -> str:
    extraction_part = DEFAULT_EXTRACTION_PROMPT.format(schema_json=schema_json)
    
    match doc_type:
        case DocumentType.INVOICE:
            return INVOICE_PROMPT + extraction_part
        case DocumentType.RECEIPT:
            return RECEIPT_PROMPT + extraction_part
        case DocumentType.FORM:
            return FORM_PROMPT + extraction_part
        case _:
            return extraction_part


ROUTER_PROMPT = """
You are a query router for a document processing system. 
You have two tools:
1. SQL: For questions about specific numbers, totals, dates, or vendor comparisons.
2. VECTOR: For questions about concepts, contents, descriptions, or "what" questions.

Analyze the query and respond with a JSON object:
{
    "route": "sql" | "vector" | "hybrid",
    "reasoning": "string",
    "sql_metadata_filter": {
        "vendor": "string or null",
        "min_amount": float or null,
        "max_amount": float or null,
        "date_after": "string or null"
    }
}

Query: {query}
"""
