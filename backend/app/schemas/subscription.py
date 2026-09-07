from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel


class SubscriptionPlanResponse(BaseModel):
    id: str
    plan_id: str
    name: str
    description: Optional[str]
    customer_type: str
    billing_type: str
    monthly_price: Decimal
    yearly_price: Decimal
    per_bill_price: Decimal
    trial_days: int
    features: Optional[str]
    limits: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime


class SubscriptionCreateRequest(BaseModel):
    plan_id: str


class SalesmanSubscriptionCreateRequest(BaseModel):
    plan_id: str
    customer_id: str


class BillingUsageCreateRequest(BaseModel):
    subscription_id: str
    invoice_id: str


class SubscriptionResponse(BaseModel):
    id: str
    subscription_id: str
    plan_id: str
    retailer_id: Optional[str]
    customer_id: Optional[str]
    salesman_id: Optional[str] = None
    status: str
    started_at: datetime
    current_period_start: datetime
    current_period_end: datetime
    trial_ends_at: Optional[datetime]
    auto_renew: bool
    cancelled_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime


class SubscriptionPaymentRequest(BaseModel):
    amount: Decimal
    payment_method: str
    transaction_reference: Optional[str] = None
    notes: Optional[str] = None


class SubscriptionCancelResponse(BaseModel):
    subscription_id: str
    status: str
    cancelled_at: Optional[datetime]


class BillingUsageResponse(BaseModel):
    id: str
    usage_id: str
    subscription_id: str
    customer_id: str
    invoice_id: str
    billing_period_start: datetime
    billing_period_end: datetime
    quantity: int
    unit_price: Decimal
    amount: Decimal
    created_at: datetime
