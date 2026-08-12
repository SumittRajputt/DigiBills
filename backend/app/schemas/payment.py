from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class PaymentCreateRequest(BaseModel):
    invoice_id: str
    amount: Decimal = Field(gt=0)
    payment_method: str = Field(min_length=1, max_length=30)
    transaction_reference: Optional[str] = Field(
        default=None,
        max_length=255,
    )
    notes: Optional[str] = None


class PaymentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    payment_id: str
    invoice_id: str
    amount: Decimal
    payment_method: str
    payment_status: str
    transaction_reference: Optional[str]
    paid_at: datetime
    refund_amount: Decimal
    refund_status: Optional[str]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime


class PaymentRefundRequest(BaseModel):
    refund_amount: Decimal = Field(gt=0)
    refund_method: Optional[str] = Field(
        default=None,
        max_length=30,
    )
    notes: Optional[str] = None


class PaymentDetailResponse(PaymentResponse):
    pass
