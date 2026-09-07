import json
from decimal import Decimal
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.subscription_plan import SubscriptionPlan


CUSTOMER_CUSTOMER_TYPE = "customer"

DEFAULT_CUSTOMER_PLANS = (
    {
        "plan_id": "CUS-MONTHLY",
        "name": "Customer Monthly",
        "description": "Monthly customer subscription plan.",
        "billing_type": "monthly",
        "monthly_price": Decimal("99.00"),
        "yearly_price": Decimal("0.00"),
        "per_bill_price": Decimal("0.00"),
        "trial_days": 7,
        "features": [],
    },
    {
        "plan_id": "CUS-YEARLY",
        "name": "Customer Yearly",
        "description": "Yearly customer subscription plan.",
        "billing_type": "yearly",
        "monthly_price": Decimal("0.00"),
        "yearly_price": Decimal("999.00"),
        "per_bill_price": Decimal("0.00"),
        "trial_days": 7,
        "features": [],
    },
    {
        "plan_id": "CUS-PER-BILL",
        "name": "Customer Pay Per Bill",
        "description": "Customer pay-per-bill subscription plan.",
        "billing_type": "per_bill",
        "monthly_price": Decimal("0.00"),
        "yearly_price": Decimal("0.00"),
        "per_bill_price": Decimal("5.00"),
        "trial_days": 0,
        "features": [],
    },
)


def ensure_customer_plans(
    db: Session,
) -> list[SubscriptionPlan]:
    plans: list[SubscriptionPlan] = []

    for definition in DEFAULT_CUSTOMER_PLANS:
        existing = db.execute(
            select(SubscriptionPlan).where(
                SubscriptionPlan.plan_id == definition["plan_id"]
            )
        ).scalar_one_or_none()

        if existing is None:
            existing = SubscriptionPlan(
                plan_id=definition["plan_id"],
                name=definition["name"],
                description=definition["description"],
                customer_type=CUSTOMER_CUSTOMER_TYPE,
                billing_type=definition["billing_type"],
                monthly_price=definition["monthly_price"],
                yearly_price=definition["yearly_price"],
                per_bill_price=definition["per_bill_price"],
                trial_days=definition["trial_days"],
                features=json.dumps(definition["features"]),
                limits=json.dumps({}),
                is_active=True,
            )
            db.add(existing)

        plans.append(existing)

    db.commit()

    for plan in plans:
        db.refresh(plan)

    return plans


def parse_json(
    value: Optional[str],
    default: Any,
) -> Any:
    if not value:
        return default

    try:
        return json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return default
