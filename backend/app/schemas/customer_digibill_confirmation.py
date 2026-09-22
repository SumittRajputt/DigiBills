from decimal import Decimal
from typing import Literal, Optional

from pydantic import BaseModel, Field


WarrantyAnswer = Literal["yes", "no", "unknown"]


class CustomerDigiBillConfirmationRequest(BaseModel):
    customer_has_warranty: WarrantyAnswer = "unknown"
    duration_value: Optional[Decimal] = Field(
        default=None,
        gt=0,
    )
    duration_unit: Optional[Literal["months", "years"]] = None
