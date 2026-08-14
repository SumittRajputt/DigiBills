from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field


class SalesReturnItemCreateRequest(BaseModel):
    invoice_item_id: str = Field(min_length=1)
    quantity: int = Field(gt=0)
    product_unit_ids: list[str] = Field(
        default_factory=list,
    )
    condition: str = Field(
        default="good",
        min_length=1,
        max_length=30,
    )
    return_to_inventory: bool = True
    restocking_fee: Decimal = Field(
        default=Decimal("0.00"),
        ge=0,
    )
    reason: Optional[str] = Field(
        default=None,
        max_length=255,
    )


class SalesReturnCreateRequest(BaseModel):
    invoice_id: str = Field(min_length=1)
    reason: Optional[str] = None
    notes: Optional[str] = None


class SalesReturnProcessRequest(BaseModel):
    refund_method: Optional[str] = Field(
        default=None,
        max_length=30,
    )


class SalesReturnItemResponse(BaseModel):
    id: str
    sales_return_id: str
    invoice_item_id: str
    product_variant_id: str
    product_name: str
    sku: Optional[str]
    quantity: int
    unit_price: Decimal
    return_amount: Decimal
    restocking_fee: Decimal
    refund_amount: Decimal
    condition: str
    return_to_inventory: bool
    reason: Optional[str]
    created_at: datetime


class SalesReturnResponse(BaseModel):
    id: str
    return_id: str
    invoice_id: str
    retailer_id: str
    customer_id: str
    processed_by_user_id: Optional[str]
    return_amount: Decimal
    refund_amount: Decimal
    refund_method: Optional[str]
    status: str
    reason: Optional[str]
    notes: Optional[str]
    requested_at: datetime
    processed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime


class SalesReturnDetailResponse(SalesReturnResponse):
    items: list[SalesReturnItemResponse]
