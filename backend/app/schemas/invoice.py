from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field


class InvoiceItemCreateRequest(BaseModel):
    sku: str = Field(min_length=1, max_length=100)
    quantity: int = Field(gt=0)
    unit_price: Optional[Decimal] = Field(
        default=None,
        gt=0,
    )
    discount_amount: Decimal = Field(
        default=Decimal("0.00"),
        ge=0,
    )


class InvoiceCreateRequest(BaseModel):
    customer_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    invoice_number: Optional[str] = Field(
        default=None,
        max_length=100,
    )
    discount_amount: Decimal = Field(
        default=Decimal("0.00"),
        ge=0,
    )
    notes: Optional[str] = None
    items: list[InvoiceItemCreateRequest] = Field(
        min_length=1,
    )


class InvoiceItemResponse(BaseModel):
    id: str
    invoice_id: str
    product_variant_id: str
    product_name: str
    sku: Optional[str]
    quantity: int
    unit_price: Decimal
    unit_cost: Optional[Decimal]
    discount_amount: Decimal
    tax_rate: Decimal
    tax_amount: Decimal
    line_total: Decimal
    created_at: datetime


class InvoiceResponse(BaseModel):
    id: str
    invoice_id: str
    retailer_id: str
    employee_id: Optional[str]
    customer_id: str
    invoice_number: Optional[str]
    invoice_date: datetime
    subtotal: Decimal
    discount_amount: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    payment_status: str
    status: str
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime


class InvoiceDetailResponse(InvoiceResponse):
    items: list[InvoiceItemResponse]