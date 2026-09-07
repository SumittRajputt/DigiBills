from typing import Any

from pydantic import BaseModel


class CustomerDashboardResponse(BaseModel):
    customer: dict[str, Any]

    total_purchases: str
    total_invoices: int
    amount_paid: str
    refunds_received: str
    outstanding_amount: str
    my_products: int
    active_warranties: int
    my_returns: int
    product_transfers: int

    invoice_status: dict[str, int]

    spending_trend: list[dict[str, Any]]
    recent_invoices: list[dict[str, Any]]
    recent_payments: list[dict[str, Any]]
    warranties: list[dict[str, Any]]
