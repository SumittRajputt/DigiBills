from typing import Optional

from pydantic import BaseModel, Field


class CustomerTransferCreateRequest(BaseModel):
    product_unit_id: Optional[str] = Field(
        default=None,
        min_length=1,
    )
    digibill_id: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=20,
    )
    to_customer_identifier: str = Field(
        min_length=1,
        max_length=255,
    )
    reason: Optional[str] = None
    payment_payer: str = Field(
        default="receiver",
        min_length=1,
        max_length=20,
    )


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


class CustomerTransferSerialVerifyRequest(BaseModel):
    digibill_id: str = Field(
        min_length=1,
        max_length=20,
    )
    serial_number: str = Field(
        min_length=1,
        max_length=255,
    )


class CustomerTransferSerialVerifyResponse(BaseModel):
    verified: bool
    status: str
    digibill_id: str
    serial_number: str
    message: str
    product: Optional[dict] = None
