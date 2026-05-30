from pydantic import BaseModel, Field


class Product(BaseModel):
    name: str
    quantity: float | None = None
    unit_price: float | None = None
    total_price: float | None = None


class StructuredInvoice(BaseModel):
    nazwa_sklepu: str | None = None
    data: str | None = None
    kwota_koncowa: float | None = Field(None, description="Total amount")
    lista_produktow: list[Product] = Field(default_factory=list)
    numer_faktury: str | None = None
    sprzedawca: str | None = None
    nabywca: str | None = None
    kwota_netto: float | None = None
    kwota_brutto: float | None = None
    VAT: float | None = None


class StructuredReceipt(BaseModel):
    nazwa_sklepu: str | None = None
    data: str | None = None
    kwota_koncowa: float | None = Field(None, description="Total amount")
    lista_produktow: list[Product] = Field(default_factory=list)
    kwota_netto: float | None = None
    kwota_brutto: float | None = None
    VAT: float | None = None


class FormField(BaseModel):
    question: str
    answer: str


class StructuredForm(BaseModel):
    data: str | None = None
    wypelniajacy: str | None = Field(None, description="Who filled the form")
    pola_formularza: list[FormField] = Field(default_factory=list, description="List of fields and their answers")


StructuredDocument = StructuredInvoice | StructuredReceipt | StructuredForm


def get_model_for_type(doc_type) -> type[BaseModel]:
    # We duck-type doc_type to avoid circular imports, but it's DocumentType enum
    if doc_type.value == "INVOICE":
        return StructuredInvoice
    elif doc_type.value == "RECEIPT":
        return StructuredReceipt
    elif doc_type.value == "FORM":
        return StructuredForm
    return StructuredInvoice
