from decimal import Decimal
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class CustomerPlanResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    plan_id: str
    name: str
    description: Optional[str]
    billing_type: str
    monthly_price: Decimal
    yearly_price: Decimal
    per_bill_price: Decimal
    trial_days: int
    features: list[Any]
    is_active: bool


class CustomerPlanUpdateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: Optional[str] = None
    billing_type: str
    monthly_price: Decimal = Field(ge=0)
    yearly_price: Decimal = Field(ge=0)
    per_bill_price: Decimal = Field(ge=0)
    trial_days: int = Field(default=0, ge=0)
    features: list[Any] = Field(default_factory=list)
    is_active: bool = True
