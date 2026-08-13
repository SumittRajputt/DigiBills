from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field


class WarrantyCreateRequest(BaseModel):
    invoice_id: str
    product_variant_id: str
    start_date: date
    end_date: date
    duration_months: int = Field(gt=0)
    is_transferable: bool = True


class WarrantyResponse(BaseModel):
    id: str
    warranty_id: str
    invoice_id: str
    product_variant_id: str
    customer_id: str
    start_date: date
    end_date: date
    duration_months: int
    is_transferable: bool
    status: str
    created_at: datetime
    updated_at: datetime


class WarrantyStatusUpdateRequest(BaseModel):
    status: str


class WarrantyTransferRequest(BaseModel):
    customer_id: str
