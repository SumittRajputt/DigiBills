from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class SupplierCreateRequest(BaseModel):
    name: str = Field(
        min_length=1,
        max_length=200,
    )

    contact_person: Optional[str] = Field(
        default=None,
        max_length=150,
    )

    phone_number: Optional[str] = Field(
        default=None,
        max_length=20,
    )

    email: Optional[EmailStr] = None

    address: Optional[str] = None

    tax_identifier: Optional[str] = Field(
        default=None,
        max_length=100,
    )


class SupplierResponse(BaseModel):
    id: str
    supplier_id: str
    retailer_id: str
    name: str
    contact_person: Optional[str] = None
    phone_number: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    tax_identifier: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime