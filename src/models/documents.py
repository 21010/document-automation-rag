from pydantic import BaseModel, Field


class Product(BaseModel):
    name: str = Field(..., description="Name of the product")
    quantity: float | None = Field(None, description="Quantity of the product")
    unit_price: float | None = Field(None, description="Price per unit of the product")
    total_price: float | None = Field(None, description="Total price of the product")


class StructuredInvoice(BaseModel):
    nazwa_sklepu: str | None = Field(None, description="Name of the store")
    data: str | None = Field(None, description="Date of the transaction")
    kwota_koncowa: float | None = Field(None, description="Total amount")
    lista_produktow: list[Product] = Field(default_factory=list)
    numer_faktury: str | None = Field(None, description="Invoice number")
    sprzedawca: str | None = Field(None, description="Seller of the invoice")
    nabywca: str | None = Field(None, description="Buyer of the invoice")
    kwota_netto: float | None = Field(None, description="Net amount")
    kwota_brutto: float | None = Field(None, description="Gross amount")
    VAT: float | None = Field(None, description="VAT amount")


class StructuredReceipt(BaseModel):
    nazwa_sklepu: str | None = Field(None, description="Name of the store")
    data: str | None = Field(None, description="Date of the transaction")
    kwota_koncowa: float | None = Field(None, description="Total amount")
    lista_produktow: list[Product] = Field(default_factory=list)
    kwota_netto: float | None = Field(None, description="Net amount")
    kwota_brutto: float | None = Field(None, description="Gross amount")
    VAT: float | None = Field(None, description="VAT amount")


class FormField(BaseModel):
    question: str = Field(..., description="Question")
    answer: str = Field(..., description="Answer")


class StructuredForm(BaseModel):
    data: str | None = Field(None, description="Date of the transaction")
    wypelniajacy: str | None = Field(None, description="Who filled the form")
    pola_formularza: list[FormField] = Field(default_factory=list, description="List of fields and their answers")


StructuredDocument = StructuredInvoice | StructuredReceipt | StructuredForm


def get_model_for_type(doc_type) -> type[StructuredInvoice] | type[StructuredReceipt] | type[StructuredForm]:
    """Returns the appropriate Pydantic model for a given document type."""
    if doc_type.value == "INVOICE":
        return StructuredInvoice
    elif doc_type.value == "RECEIPT":
        return StructuredReceipt
    elif doc_type.value == "FORM":
        return StructuredForm
    return StructuredInvoice
