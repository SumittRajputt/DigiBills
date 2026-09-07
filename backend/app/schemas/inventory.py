from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field


class InventoryItemCreateRequest(BaseModel):
    location_id: str

    sku: str = Field(
        min_length=1,
        max_length=100,
    )

    reorder_level: int = Field(
        default=0,
        ge=0,
    )

    reorder_quantity: int = Field(
        default=0,
        ge=0,
    )

    average_cost: Decimal = Field(
        default=Decimal("0"),
        ge=0,
        decimal_places=2,
    )

    # Retailer-controlled GST rate.
    # If omitted, the product variant's default tax rate is used.
    tax_rate: Optional[Decimal] = Field(
        default=None,
        ge=0,
        le=100,
        decimal_places=2,
    )


class InventoryItemUpdateRequest(BaseModel):
    # Retailer can change GST for an existing inventory item.
    tax_rate: Decimal = Field(
        ge=0,
        le=100,
        decimal_places=2,
    )


class InventoryItemResponse(BaseModel):
    id: str
    retailer_id: str
    location_id: str
    product_variant_id: str
    quantity_on_hand: int
    quantity_reserved: int
    quantity_available: int
    reorder_level: int
    reorder_quantity: int
    average_cost: Decimal
    tax_rate: Decimal
    last_stocked_at: Optional[datetime]
    updated_at: datetime
