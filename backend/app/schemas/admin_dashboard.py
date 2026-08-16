from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class SalesOverviewItem(BaseModel):
    date: str
    amount: str


class TopRetailerItem(BaseModel):
    business_name: str
    sales: str


class PaymentMethodItem(BaseModel):
    method: str
    amount: str
    percentage: str


class RecentActivityItem(BaseModel):
    action: str
    entity_type: str
    description: Optional[str]
    created_at: datetime


class AdminDashboardResponse(BaseModel):
    total_retailers: int
    active_retailers: int
    pending_approvals: int
    total_customers: int
    total_invoices: int
    total_sales: str
    payments_collected: str
    refunds: str
    returns: str
    outstanding_amount: str
    sales_overview: list[SalesOverviewItem]
    top_retailers: list[TopRetailerItem]
    payment_methods: list[PaymentMethodItem]
    recent_activity: list[RecentActivityItem]
