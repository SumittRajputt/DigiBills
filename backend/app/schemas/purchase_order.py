from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field


class PurchaseOrderCreateRequest(BaseModel):
    supplier_id: str = Field(
        min_length=1,
        max_length=30,
    )

    location_id: str

    expected_delivery_date: Optional[datetime] = None

    notes: Optional[str] = None


class PurchaseOrderItemCreateRequest(BaseModel):
    sku: str = Field(
        min_length=1,
        max_length=100,
    )

    ordered_quantity: int = Field(
        gt=0,
    )

    unit_cost: Decimal = Field(
        ge=0,
        decimal_places=2,
    )

    tax_rate: Decimal = Field(
        default=Decimal("0"),
        ge=0,
        decimal_places=2,
    )


class PurchaseOrderResponse(BaseModel):
    id: str
    purchase_order_id: str
    retailer_id: str
    supplier_id: str
    location_id: str
    created_by_user_id: Optional[str] = None
    status: str
    subtotal: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    expected_delivery_date: Optional[datetime] = None
    received_at: Optional[datetime] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class PurchaseOrderItemResponse(BaseModel):
    id: str
    purchase_order_id: str
    product_variant_id: str
    product_name: str
    sku: Optional[str] = None
    ordered_quantity: int
    received_quantity: int
    unit_cost: Decimal
    tax_rate: Decimal
    tax_amount: Decimal
    line_total: Decimal
    received_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

class PurchaseOrderReceiveRequest(BaseModel):
    received_quantity: int = Field(
        gt=0,
    )