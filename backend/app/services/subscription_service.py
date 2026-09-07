import uuid
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.billing_usage import BillingUsage
from app.models.customer import Customer
from app.models.invoice import Invoice
from app.models.retailer import Retailer
from app.models.subscription import Subscription
from app.models.subscription_plan import SubscriptionPlan
from app.services.invoice_service import create_subscription_invoice


def generate_subscription_id() -> str:
    return f"SUB-{uuid.uuid4().hex[:10].upper()}"


def generate_usage_id() -> str:
    return f"USE-{uuid.uuid4().hex[:10].upper()}"


def get_plan_by_reference(
    db: Session,
    plan_reference: str,
) -> Optional[SubscriptionPlan]:
    statement = select(SubscriptionPlan).where(
        SubscriptionPlan.plan_id == plan_reference
    )

    return db.execute(
        statement
    ).scalar_one_or_none()


def get_subscription_by_reference(
    db: Session,
    subscription_reference: str,
) -> Optional[Subscription]:
    statement = select(Subscription).where(
        Subscription.subscription_id == subscription_reference
    )

    return db.execute(
        statement
    ).scalar_one_or_none()


def get_active_subscription_for_retailer(
    db: Session,
    retailer_id: uuid.UUID,
) -> Optional[Subscription]:
    statement = select(Subscription).where(
        Subscription.retailer_id == retailer_id,
        Subscription.status.in_(
            ["trialing", "active"]
        ),
    )

    return db.execute(
        statement
    ).scalar_one_or_none()


def get_active_subscription_for_customer(
    db: Session,
    customer_id: uuid.UUID,
) -> Optional[Subscription]:
    statement = select(Subscription).where(
        Subscription.customer_id == customer_id,
        Subscription.status.in_(
            ["trialing", "active"]
        ),
    )

    return db.execute(
        statement
    ).scalar_one_or_none()


def get_current_subscription_for_customer(
    db: Session,
    customer_id: uuid.UUID,
) -> Optional[Subscription]:
    statement = (
        select(Subscription)
        .where(
            Subscription.customer_id == customer_id,
            Subscription.status.in_(
                ["pending_payment", "trialing", "active"]
            ),
        )
        .order_by(Subscription.created_at.desc())
    )

    return db.execute(
        statement
    ).scalars().first()


def validate_plan(
    plan: SubscriptionPlan,
    expected_customer_type: str,
) -> None:
    if not plan.is_active:
        raise ValueError(
            "Subscription plan is not active."
        )

    if plan.customer_type != expected_customer_type:
        raise ValueError(
            "Subscription plan is not available for this account type."
        )

    valid_billing_types = {
        "monthly",
        "yearly",
        "per_bill",
    }

    if plan.billing_type not in valid_billing_types:
        raise ValueError(
            "Invalid subscription billing type."
        )

    if plan.billing_type == "monthly":
        if plan.monthly_price <= Decimal("0.00"):
            raise ValueError(
                "Monthly subscription price must be greater than zero."
            )

    elif plan.billing_type == "yearly":
        if plan.yearly_price <= Decimal("0.00"):
            raise ValueError(
                "Yearly subscription price must be greater than zero."
            )

    elif plan.billing_type == "per_bill":
        if plan.per_bill_price <= Decimal("0.00"):
            raise ValueError(
                "Per-bill subscription price must be greater than zero."
            )


def create_subscription(
    db: Session,
    plan: SubscriptionPlan,
    retailer_id: Optional[uuid.UUID] = None,
    customer_id: Optional[uuid.UUID] = None,
    salesman_id: Optional[uuid.UUID] = None,
) -> Subscription:
    if (retailer_id is None) == (customer_id is None):
        raise ValueError(
            "Subscription must belong to exactly one retailer or customer."
        )

    if salesman_id is not None:
        from app.models.employee import Employee

        salesman = db.execute(
            select(Employee).where(
                Employee.id == salesman_id,
                Employee.employee_type == "salesman",
                Employee.status == "active",
            )
        ).scalar_one_or_none()

        if salesman is None:
            raise ValueError(
                "Active salesman not found."
            )

        if retailer_id is not None and salesman.retailer_id != retailer_id:
            raise ValueError(
                "Salesman does not belong to this retailer."
            )

        if customer_id is None:
            raise ValueError(
                "Salesman can only be assigned to a customer subscription."
            )

    if retailer_id is not None:
        validate_plan(plan, "retailer")

        existing = get_active_subscription_for_retailer(
            db,
            retailer_id,
        )

        if existing is not None:
            raise ValueError(
                "Retailer already has an active subscription."
            )

    else:
        validate_plan(plan, "customer")

        existing = get_active_subscription_for_customer(
            db,
            customer_id,
        )

        if existing is not None:
            raise ValueError(
                "Customer already has an active subscription."
            )

    now = datetime.now(timezone.utc)

    if plan.billing_type == "monthly":
        period_end = now + timedelta(days=30)

    elif plan.billing_type == "yearly":
        period_end = now + timedelta(days=365)

    else:
        # Per-bill plans don't have a recurring calendar period.
        period_end = now

    trial_ends_at = None

    if plan.trial_days > 0:
        trial_ends_at = now + timedelta(
            days=plan.trial_days
        )
        status = "trialing"
    else:
        # A paid monthly/yearly subscription with no trial
        # must not become active before payment.
        status = "pending_payment"

    subscription = Subscription(
        subscription_id=generate_subscription_id(),
        plan_id=plan.id,
        retailer_id=retailer_id,
        customer_id=customer_id,
        salesman_id=salesman_id,
        status=status,
        started_at=now,
        current_period_start=now,
        current_period_end=period_end,
        trial_ends_at=trial_ends_at,
        auto_renew=True,
    )

    db.add(subscription)
    db.flush()

    # Customer monthly/yearly plans with zero trial require
    # payment before the subscription becomes active.
    if (
        customer_id is not None
        and plan.trial_days == 0
        and plan.billing_type in {"monthly", "yearly"}
    ):
        create_subscription_invoice(
            db=db,
            subscription=subscription,
            plan=plan,
            billing_period_start=now,
            billing_period_end=period_end,
        )

    db.commit()
    db.refresh(subscription)

    return subscription


def cancel_subscription(
    db: Session,
    subscription: Subscription,
) -> Subscription:
    if subscription.status in {
        "cancelled",
        "expired",
    }:
        raise ValueError(
            "Subscription is already inactive."
        )

    subscription.status = "cancelled"
    subscription.cancelled_at = datetime.now(
        timezone.utc
    )
    subscription.auto_renew = False
    subscription.updated_at = datetime.now(
        timezone.utc
    )

    db.commit()
    db.refresh(subscription)

    return subscription


def create_billing_usage(
    db: Session,
    subscription: Subscription,
    invoice: Invoice,
) -> BillingUsage:
    if subscription.customer_id is None:
        raise ValueError(
            "Only customer subscriptions can generate bill usage."
        )

    if subscription.status not in {
        "trialing",
        "active",
    }:
        raise ValueError(
            "Subscription is not active."
        )

    if invoice.customer_id != subscription.customer_id:
        raise ValueError(
            "Invoice does not belong to the subscription customer."
        )

    plan = db.execute(
        select(SubscriptionPlan).where(
            SubscriptionPlan.id == subscription.plan_id
        )
    ).scalar_one_or_none()

    if plan is None:
        raise ValueError(
            "Subscription plan not found."
        )

    if plan.billing_type != "per_bill":
        raise ValueError(
            "Billing usage is only available for per-bill plans."
        )

    existing = db.execute(
        select(BillingUsage).where(
            BillingUsage.subscription_id == subscription.id,
            BillingUsage.invoice_id == invoice.id,
        )
    ).scalar_one_or_none()

    if existing is not None:
        raise ValueError(
            "Billing usage already exists for this invoice."
        )

    unit_price = Decimal(
        plan.per_bill_price
    )

    now = datetime.now(timezone.utc)

    usage = BillingUsage(
        usage_id=generate_usage_id(),
        subscription_id=subscription.id,
        customer_id=subscription.customer_id,
        invoice_id=invoice.id,
        billing_period_start=now,
        billing_period_end=now,
        quantity=1,
        unit_price=unit_price,
        amount=unit_price,
    )

    db.add(usage)
    db.commit()
    db.refresh(usage)

    return usage



def create_or_get_renewal_invoice(
    db: Session,
    subscription: Subscription,
    plan: SubscriptionPlan,
    billing_period_start: datetime,
    billing_period_end: datetime,
):
    return create_subscription_invoice(
        db=db,
        subscription=subscription,
        plan=plan,
        billing_period_start=billing_period_start,
        billing_period_end=billing_period_end,
    )


def process_subscription_lifecycle(
    db: Session,
) -> dict:
    """
    Process customer subscription trials, payments, renewals,
    and expiration.

    Customer monthly/yearly subscriptions require payment
    before becoming active.

    Trialing subscriptions receive the subscription benefit
    during the trial. When the trial ends, a subscription
    invoice is created. The subscription remains pending
    until that invoice is paid.

    Active subscriptions receive the subscription benefit
    until the current billing period ends. A renewal invoice
    is then created. The next period only becomes active
    after that invoice is paid.

    Per-bill plans do not participate in this calendar lifecycle.
    """

    now = datetime.now(timezone.utc)

    statement = (
        select(Subscription)
        .where(
            Subscription.status.in_(
                ["pending_payment", "trialing", "active"]
            )
        )
        .with_for_update()
    )

    subscriptions = list(
        db.execute(statement).scalars().all()
    )

    trial_invoices = 0
    renewed = 0
    expired = 0
    skipped_per_bill = 0

    for subscription in subscriptions:

        plan = db.execute(
            select(SubscriptionPlan).where(
                SubscriptionPlan.id
                == subscription.plan_id
            )
        ).scalar_one_or_none()

        if plan is None:
            continue

        # Per-bill is not a customer calendar subscription.
        if plan.billing_type == "per_bill":
            skipped_per_bill += 1
            continue

        current_period_end = subscription.current_period_end

        if current_period_end.tzinfo is None:
            current_period_end = current_period_end.replace(
                tzinfo=timezone.utc
            )

        trial_ends_at = subscription.trial_ends_at

        if (
            trial_ends_at is not None
            and trial_ends_at.tzinfo is None
        ):
            trial_ends_at = trial_ends_at.replace(
                tzinfo=timezone.utc
            )

        # --------------------------------------------------
        # 1. Zero-day subscription waiting for first payment
        # --------------------------------------------------
        if subscription.status == "pending_payment":

            # If the first billing period has already ended
            # without payment, expire the subscription.
            if current_period_end <= now:
                subscription.status = "expired"
                subscription.auto_renew = False
                subscription.updated_at = now
                expired += 1

            continue

        # --------------------------------------------------
        # 2. Trial has ended
        # --------------------------------------------------
        if (
            subscription.status == "trialing"
            and trial_ends_at is not None
            and trial_ends_at <= now
        ):
            existing_invoice = db.execute(
                select(Invoice).where(
                    Invoice.subscription_id
                    == subscription.id,
                    Invoice.billing_period_start
                    == subscription.current_period_start,
                    Invoice.billing_period_end
                    == subscription.current_period_end,
                )
            ).scalar_one_or_none()

            if existing_invoice is None:
                create_or_get_renewal_invoice(
                    db=db,
                    subscription=subscription,
                    plan=plan,
                    billing_period_start=(
                        subscription.current_period_start
                    ),
                    billing_period_end=(
                        subscription.current_period_end
                    ),
                )
                trial_invoices += 1

            # Do not activate until the subscription invoice
            # has actually been paid.
            subscription.status = "pending_payment"
            subscription.updated_at = now

            continue

        # --------------------------------------------------
        # 3. Active subscription period has ended
        # --------------------------------------------------
        if (
            subscription.status == "active"
            and current_period_end <= now
        ):

            if plan.billing_type == "monthly":
                period_days = 30
            elif plan.billing_type == "yearly":
                period_days = 365
            else:
                continue

            next_period_start = current_period_end
            next_period_end = (
                next_period_start
                + timedelta(days=period_days)
            )

            existing_invoice = db.execute(
                select(Invoice).where(
                    Invoice.subscription_id
                    == subscription.id,
                    Invoice.billing_period_start
                    == next_period_start,
                    Invoice.billing_period_end
                    == next_period_end,
                )
            ).scalar_one_or_none()

            if existing_invoice is None:
                create_or_get_renewal_invoice(
                    db=db,
                    subscription=subscription,
                    plan=plan,
                    billing_period_start=next_period_start,
                    billing_period_end=next_period_end,
                )

                # The current subscription period has ended.
                # It must not continue receiving benefits while
                # waiting for payment.
                subscription.status = "pending_payment"
                subscription.auto_renew = True
                subscription.updated_at = now

                renewed += 1

            else:
                # Renewal invoice already exists and is unpaid.
                # Keep subscription out of active state.
                if existing_invoice.payment_status != "paid":
                    subscription.status = "pending_payment"
                    subscription.updated_at = now

    db.commit()

    return {
        "trial_invoices": trial_invoices,
        "renewed": renewed,
        "expired": expired,
        "skipped_per_bill": skipped_per_bill,
    }

