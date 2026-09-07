from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class SalesOverviewItem(BaseModel):
    date: str
    amount: str


class PaymentMethodItem(BaseModel):
    method: str
    amount: str
    percentage: str


class RecentInvoiceItem(BaseModel):
    invoice_id: str
    customer_id: str
    invoice_number: Optional[str]
    total_amount: str
    payment_status: str
    status: str
    invoice_date: datetime


class RecentPaymentItem(BaseModel):
    payment_id: str
    invoice_id: str
    amount: str
    payment_method: str
    payment_status: str
    paid_at: datetime


class LowStockItem(BaseModel):
    product_variant_id: str
    sku: str
    variant_name: str
    quantity_on_hand: int
    quantity_reserved: int
    quantity_available: int
    reorder_level: int


class RetailerDashboardResponse(BaseModel):
    total_customers: int
    total_invoices: int
    total_sales: str
    payments_collected: str
    outstanding_amount: str

    paid_invoices: int
    partial_invoices: int
    unpaid_invoices: int

    sales_overview: list[SalesOverviewItem]
    payment_methods: list[PaymentMethodItem]
    recent_invoices: list[RecentInvoiceItem]
    recent_payments: list[RecentPaymentItem]
    low_stock_items: list[LowStockItem]
