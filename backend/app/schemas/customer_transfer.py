from typing import Optional

from pydantic import BaseModel, Field


class CustomerTransferCreateRequest(BaseModel):
    product_unit_id: str = Field(min_length=1)
    to_customer_identifier: str = Field(
        min_length=1,
        max_length=255,
    )
    reason: Optional[str] = None


class CustomerTransferPayRequest(BaseModel):
    payment_method: str = Field(
        min_length=1,
        max_length=30,
    )
    transaction_reference: Optional[str] = Field(
        default=None,
        max_length=255,
    )


class CustomerTransferAcceptRequest(BaseModel):
    confirmation: bool = True


class CustomerTransferRejectRequest(BaseModel):
    rejection_reason: str = Field(
        min_length=1,
        max_length=1000,
    )
