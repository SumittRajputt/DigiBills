from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.payment_configuration import PaymentConfiguration


DEFAULT_PER_BILL_CHARGE = Decimal("9.00")
DEFAULT_CUSTOMER_BILL_CHARGE = Decimal("5.00")
DEFAULT_CUSTOMER_TRANSFER_FEE = Decimal("9.00")
DEFAULT_MAX_CASH_DUE_INVOICES = 20
DEFAULT_ANNUAL_SUBSCRIPTION_PRICE = Decimal("0.00")
DEFAULT_SALESMAN_COMMISSION_PERCENT = Decimal("20.00")


def get_payment_configuration(
    db: Session,
) -> PaymentConfiguration:
    configuration = db.execute(
        select(PaymentConfiguration).limit(1)
    ).scalar_one_or_none()

    if configuration is not None:
        return configuration

    configuration = PaymentConfiguration(
        per_bill_charge=DEFAULT_PER_BILL_CHARGE,
        customer_bill_charge=DEFAULT_CUSTOMER_BILL_CHARGE,
        customer_transfer_fee=DEFAULT_CUSTOMER_TRANSFER_FEE,
        max_cash_due_invoices=DEFAULT_MAX_CASH_DUE_INVOICES,
        annual_subscription_price=(
            DEFAULT_ANNUAL_SUBSCRIPTION_PRICE
        ),
        salesman_commission_percent=(
            DEFAULT_SALESMAN_COMMISSION_PERCENT
        ),
    )

    db.add(configuration)
    db.commit()
    db.refresh(configuration)

    return configuration


def update_payment_configuration(
    db: Session,
    *,
    per_bill_charge: Decimal,
    customer_bill_charge: Decimal,
    customer_transfer_fee: Decimal,
    max_cash_due_invoices: int,
    annual_subscription_price: Decimal,
    salesman_commission_percent: Decimal,
) -> PaymentConfiguration:
    configuration = get_payment_configuration(db)

    configuration.per_bill_charge = per_bill_charge
    configuration.customer_bill_charge = customer_bill_charge
    configuration.customer_transfer_fee = customer_transfer_fee
    configuration.max_cash_due_invoices = max_cash_due_invoices
    configuration.annual_subscription_price = (
        annual_subscription_price
    )
    configuration.salesman_commission_percent = (
        salesman_commission_percent
    )

    db.commit()
    db.refresh(configuration)

    return configuration
