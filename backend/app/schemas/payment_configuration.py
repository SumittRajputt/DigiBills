from decimal import Decimal

from pydantic import BaseModel, Field


class PaymentConfigurationResponse(BaseModel):
    id: str
    per_bill_charge: Decimal
    customer_bill_charge: Decimal
    customer_transfer_fee: Decimal
    max_cash_due_invoices: int
    annual_subscription_price: Decimal
    salesman_commission_percent: Decimal


class PaymentConfigurationUpdateRequest(BaseModel):
    per_bill_charge: Decimal = Field(
        ge=0,
        decimal_places=2,
    )
    customer_bill_charge: Decimal = Field(
        ge=0,
        decimal_places=2,
    )
    customer_transfer_fee: Decimal = Field(
        ge=0,
        decimal_places=2,
    )
    max_cash_due_invoices: int = Field(
        ge=0,
    )
    annual_subscription_price: Decimal = Field(
        ge=0,
        decimal_places=2,
    )
    salesman_commission_percent: Decimal = Field(
        ge=0,
        le=100,
        decimal_places=2,
    )
