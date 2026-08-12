from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ProductCreateRequest(BaseModel):
    product_code: str = Field(
        min_length=1,
        max_length=50,
    )

    name: str = Field(
        min_length=2,
        max_length=200,
    )

    brand: Optional[str] = Field(
        default=None,
        max_length=100,
    )

    category: Optional[str] = Field(
        default=None,
        max_length=100,
    )

    description: Optional[str] = None

    is_transferable: bool = True


class ProductResponse(BaseModel):
    id: str
    product_code: str
    name: str
    brand: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    is_transferable: bool
    status: str
    created_at: datetime
    updated_at: datetime