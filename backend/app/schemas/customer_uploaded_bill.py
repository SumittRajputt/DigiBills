from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class CustomerUploadedBillResponse(BaseModel):
    id: UUID
    bill_id: str
    original_filename: str
    content_type: str
    file_size: int
    amount: Decimal
    payment_status: str
    status: str
    razorpay_order_id: Optional[str] = None
    razorpay_payment_id: Optional[str] = None
    uploaded_at: datetime

    class Config:
        from_attributes = True
