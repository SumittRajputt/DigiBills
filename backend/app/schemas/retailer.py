from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class RetailerCreateRequest(BaseModel):
    business_name: str = Field(
        min_length=2,
        max_length=255,
    )

    business_type: str = Field(
        min_length=2,
        max_length=100,
    )

    phone_number: str = Field(
        min_length=10,
        max_length=20,
    )

    email: Optional[EmailStr] = None

    address: Optional[str] = Field(
        default=None,
        max_length=1000,
    )


class RetailerResponse(BaseModel):
    id: str
    retailer_id: str
    owner_user_id: str
    business_name: str
    business_type: str
    phone_number: str
    email: Optional[str] = None
    address: Optional[str] = None
    status: str
    approved_at: Optional[datetime] = None
    approved_by: Optional[str] = None
    rejection_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime