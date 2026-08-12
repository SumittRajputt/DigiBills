from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class PurchaseReturnCreateRequest(BaseModel):
    purchase_order_id: str = Field(
        min_length=1,
        max_length=30,
    )

    reason: Optional[str] = None

    notes: Optional[str] = None


class PurchaseReturnItemCreateRequest(BaseModel):
    purchase_order_item_id: str

    quantity: int = Field(
        gt=0,
    )

    reason: Optional[str] = None

    condition: str = Field(
        default="good",
        min_length=1,
        max_length=30,
    )


class PurchaseReturnResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: str
    return_id: str

    purchase_order_id: str
    retailer_id: str
    supplier_id: str
    location_id: str

    processed_by_user_id: Optional[str]

    return_amount: Decimal

    status: str

    reason: Optional[str]
    notes: Optional[str]

    requested_at: datetime
    processed_at: Optional[datetime]

    created_at: datetime
    updated_at: datetime


class PurchaseReturnItemResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: str

    purchase_return_id: str
    purchase_order_item_id: str
    product_variant_id: str

    product_name: str
    sku: Optional[str]

    quantity: int

    unit_cost: Decimal
    return_amount: Decimal

    reason: Optional[str]

    condition: str

    created_at: datetime