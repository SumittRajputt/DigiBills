from datetime import datetime
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


class CustomerResponse(BaseModel):
    id: str
    customer_id: str
    user_id: str
    full_name: str
    phone_number: str
    email: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime