from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class ProductUnitCreateRequest(BaseModel):
    product_variant_id: str
    serial_number: str
    status: str = "in_stock"


class ProductUnitResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    product_variant_id: str
    serial_number: str
    status: str
    created_at: datetime
    updated_at: datetime
