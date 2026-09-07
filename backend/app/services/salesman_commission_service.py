from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.salesman_commission import SalesmanCommission
from app.models.subscription import Subscription
from app.models.invoice import Invoice
from app.services.payment_configuration_service import (
    get_payment_configuration,
)


def create_salesman_commission_for_subscription(
    db: Session,
    subscription: Subscription,
    invoice: Invoice,
):
    """
    Create the DigiBills company-paid commission for a salesman-attributed
    customer subscription after the subscription invoice is fully paid.

    Commission is created only once per subscription.
    """

    # Subscription was not sold by a salesman.
    if subscription.salesman_id is None:
        return None

    sale_amount = Decimal(str(invoice.total_amount or 0))

    if sale_amount <= 0:
        return None

    # Prevent duplicate commission records for the same subscription.
    existing = db.execute(
        select(SalesmanCommission).where(
            SalesmanCommission.subscription_id == subscription.id
        )
    ).scalar_one_or_none()

    if existing is not None:
        return existing

    configuration = get_payment_configuration(db)

    commission_rate = Decimal(
        str(configuration.salesman_commission_percent)
    )

    if commission_rate <= 0:
        return None

    commission_amount = (
        sale_amount * commission_rate / Decimal("100")
    ).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )

    commission = SalesmanCommission(
        salesman_id=subscription.salesman_id,
        subscription_id=subscription.id,
        sale_amount=sale_amount,
        commission_rate=commission_rate,
        commission_amount=commission_amount,
        paid_amount=Decimal("0.00"),
        pending_amount=commission_amount,
        status="pending",
    )

    db.add(commission)
    db.flush()

    return commission
