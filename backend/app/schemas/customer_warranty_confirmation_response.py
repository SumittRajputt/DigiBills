from datetime import date
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict


class CustomerWarrantyConfirmationResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    has_warranty: str
    provider: Optional[str] = None
    warranty_type: Optional[str] = None
    start_date: Optional[date] = None

    duration: Optional[str] = None
    duration_value: Optional[Decimal] = None
    duration_unit: Optional[str] = None

    end_date: Optional[date] = None

    warranty_number: Optional[str] = None
    important_terms: Optional[str] = None

    confirmed: bool = False
