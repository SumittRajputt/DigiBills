from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class InventoryLocationCreateRequest(BaseModel):
    name: str = Field(
        min_length=2,
        max_length=150,
    )

    location_type: str = Field(
        min_length=2,
        max_length=50,
    )

    address: Optional[str] = None


class InventoryLocationResponse(BaseModel):
    id: str
    retailer_id: str
    name: str
    location_type: str
    address: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime