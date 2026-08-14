from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ProductOwnershipCreateRequest(BaseModel):
    invoice_id: str = Field(min_length=1)
    invoice_item_id: str = Field(min_length=1)
    product_unit_id: str = Field(min_length=1)


class ProductOwnershipResponse(BaseModel):
    id: str
    product_unit_id: str
    customer_id: str
    ownership_status: str
    acquired_at: datetime
    released_at: Optional[datetime]
    source: str
    created_at: datetime
