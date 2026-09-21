from datetime import date
from decimal import Decimal
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


WarrantyAnswer = Literal["yes", "no", "unknown"]


class WarrantyConfirmation(BaseModel):
    """
    Customer confirmation data for warranty creation.

    Bill-derived information should be prefilled by the system.
    The customer is only asked for information that is missing
    or needs confirmation.
    """

    model_config = ConfigDict(extra="forbid")

    # Whether the customer confirms that the product has warranty.
    has_warranty: WarrantyAnswer = "unknown"

    # Extracted from bill when available.
    provider: Optional[str] = None

    # manufacturer / seller / extended / other
    warranty_type: Optional[str] = None

    # Invoice date is normally used as the warranty start date.
    start_date: Optional[date] = None

    # Customer provides this only when it was not found on the bill.
    duration_value: Optional[Decimal] = Field(default=None, gt=0)

    # months / years
    duration_unit: Optional[Literal["months", "years"]] = None

    # Automatically calculated by backend.
    end_date: Optional[date] = None

    # Extracted from bill when available.
    warranty_number: Optional[str] = None

    # Extracted from bill when available.
    important_terms: Optional[str] = None

    # Customer confirmation timestamp can be added later.
    confirmed: bool = False
