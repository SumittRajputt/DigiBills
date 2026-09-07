from decimal import Decimal
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class PlanLimit(BaseModel):
    unlimited: bool = False
    limit: Optional[int] = Field(default=None, ge=0)


class RetailerPlanResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    plan_id: str
    name: str
    description: Optional[str]
    billing_type: str
    monthly_price: Decimal
    yearly_price: Decimal
    trial_days: int
    features: list[Any]
    limits: dict[str, PlanLimit]
    is_active: bool


class RetailerPlanUpdateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: Optional[str] = None
    billing_type: str
    monthly_price: Decimal = Field(ge=0)
    yearly_price: Decimal = Field(ge=0)
    trial_days: int = Field(default=0, ge=0)
    features: list[Any] = Field(default_factory=list)
    limits: dict[str, PlanLimit]
    is_active: bool = True
