from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field


class StockMovementCreateRequest(BaseModel):
    location_id: str

    sku: str = Field(
        min_length=1,
        max_length=100,
    )

    movement_type: str = Field(
        min_length=1,
        max_length=50,
    )

    quantity: int = Field(
        gt=0,
    )

    unit_cost: Optional[Decimal] = Field(
        default=None,
        ge=0,
        decimal_places=2,
    )

    reference_type: Optional[str] = Field(
        default=None,
        max_length=50,
    )

    reference_id: Optional[str] = None

    notes: Optional[str] = None


class StockMovementResponse(BaseModel):
    id: str
    retailer_id: str
    location_id: str
    product_variant_id: str
    movement_type: str
    quantity: int
    unit_cost: Optional[Decimal] = None
    reference_type: Optional[str] = None
    reference_id: Optional[str] = None
    performed_by_user_id: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime