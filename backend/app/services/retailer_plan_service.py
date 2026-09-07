import json
from decimal import Decimal
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.subscription_plan import SubscriptionPlan


RETAILER_CUSTOMER_TYPE = "retailer"

DEFAULT_RETAILER_PLANS = (
    {
        "plan_id": "retailer_basic",
        "name": "Basic",
        "description": "Basic retailer subscription plan.",
        "billing_type": "monthly",
        "monthly_price": Decimal("0.00"),
        "yearly_price": Decimal("0.00"),
        "trial_days": 0,
        "features": [],
        "limits": {},
    },
    {
        "plan_id": "retailer_plus",
        "name": "Plus",
        "description": "Plus retailer subscription plan.",
        "billing_type": "monthly",
        "monthly_price": Decimal("0.00"),
        "yearly_price": Decimal("0.00"),
        "trial_days": 0,
        "features": [],
        "limits": {},
    },
    {
        "plan_id": "retailer_pro",
        "name": "Pro",
        "description": "Pro retailer subscription plan.",
        "billing_type": "monthly",
        "monthly_price": Decimal("0.00"),
        "yearly_price": Decimal("0.00"),
        "trial_days": 0,
        "features": [],
        "limits": {},
    },
)


def ensure_retailer_plans(db: Session) -> list[SubscriptionPlan]:
    plans: list[SubscriptionPlan] = []

    for definition in DEFAULT_RETAILER_PLANS:
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
                customer_type=RETAILER_CUSTOMER_TYPE,
                billing_type=definition["billing_type"],
                monthly_price=definition["monthly_price"],
                yearly_price=definition["yearly_price"],
                per_bill_price=Decimal("0.00"),
                trial_days=definition["trial_days"],
                features=json.dumps(definition["features"]),
                limits=json.dumps(definition["limits"]),
                is_active=True,
            )
            db.add(existing)

        plans.append(existing)

    db.commit()

    for plan in plans:
        db.refresh(plan)

    return plans


def parse_json(value: Optional[str], default: Any) -> Any:
    if not value:
        return default

    try:
        return json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return default
