from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class CustomerCreateRequest(BaseModel):
    full_name: str = Field(
        min_length=2,
        max_length=150,
    )

    phone_number: str = Field(
        min_length=10,
        max_length=20,
    )

    email: Optional[EmailStr] = None


class CustomerUpdateRequest(BaseModel):
    full_name: str = Field(
        min_length=2,
        max_length=150,
    )

    phone_number: str = Field(
        min_length=10,
        max_length=20,
    )

    email: Optional[EmailStr] = None

    profile_image_url: Optional[str] = Field(
        default=None,
        max_length=500,
    )

    date_of_birth: Optional[date] = None


class CustomerResponse(BaseModel):
    id: str
    customer_id: str
    user_id: str
    full_name: str
    phone_number: str
    email: Optional[str] = None
    profile_image_url: Optional[str] = None
    date_of_birth: Optional[date] = None
    status: str
    created_at: datetime
    updated_at: datetime