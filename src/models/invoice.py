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
