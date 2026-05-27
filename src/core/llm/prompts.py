# pyrefly: ignore [missing-import]
from src.core.constants import DocumentType

DEFAULT_EXTRACTION_PROMPT = """
Extract structured information from the following document text. 
Return ONLY a JSON object matching this schema:
{
    "nazwa_sklepu": "string",
    "data": "string",
    "kwota_koncowa": float,
    "lista_produktow": [
        {"name": "string", "quantity": float, "unit_price": float, "total_price": float}
    ],
    "numer_faktury": "string",
    "sprzedawca": "string",
    "nabywca": "string",
    "kwota_netto": float,
    "kwota_brutto": float,
    "VAT": float
}
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


def get_prompt_for_type(doc_type: DocumentType) -> str:
    match doc_type:
        case DocumentType.INVOICE:
            return INVOICE_PROMPT + DEFAULT_EXTRACTION_PROMPT
        case DocumentType.RECEIPT:
            return RECEIPT_PROMPT + DEFAULT_EXTRACTION_PROMPT
        case DocumentType.FORM:
            return FORM_PROMPT + DEFAULT_EXTRACTION_PROMPT
        case _:
            return DEFAULT_EXTRACTION_PROMPT


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
