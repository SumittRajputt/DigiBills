from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field


class ProductVariantCreateRequest(BaseModel):
    product_code: str = Field(
        min_length=1,
        max_length=50,
    )

    sku: str = Field(
        min_length=1,
        max_length=100,
    )

    barcode: Optional[str] = Field(
        default=None,
        max_length=100,
    )

    variant_name: str = Field(
        min_length=1,
        max_length=200,
    )

    selling_price: Decimal = Field(
        gt=0,
        decimal_places=2,
    )

    purchase_cost: Optional[Decimal] = Field(
        default=None,
        ge=0,
        decimal_places=2,
    )

    tax_rate: Decimal = Field(
        default=Decimal("0"),
        ge=0,
        le=100,
        decimal_places=2,
    )

    track_inventory: bool = True

    requires_serial_number: bool = False


class ProductVariantResponse(BaseModel):
    id: str
    product_id: str
    sku: str
    barcode: Optional[str] = None
    variant_name: str
    selling_price: Decimal
    purchase_cost: Optional[Decimal] = None
    tax_rate: Decimal
    track_inventory: bool
    requires_serial_number: bool
    status: str