from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ProductTransferCreateRequest(BaseModel):
    product_unit_id: str = Field(min_length=1)
    from_customer_id: str = Field(min_length=1)
    to_customer_id: str = Field(min_length=1)
    reason: Optional[str] = None


class ProductTransferRejectRequest(BaseModel):
    rejection_reason: str = Field(min_length=1)


class ProductTransferResponse(BaseModel):
    id: str
    transfer_id: str
    product_unit_id: str
    from_customer_id: str
    to_customer_id: str
    requested_by_user_id: str
    approved_by_user_id: Optional[str]
    status: str
    reason: Optional[str]
    rejection_reason: Optional[str]
    requested_at: datetime
    approved_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
