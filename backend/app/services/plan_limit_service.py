import json
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.invoice import Invoice
from app.models.product import Product
from app.models.subscription import Subscription
from app.models.subscription_plan import SubscriptionPlan
from app.services.subscription_service import (
    get_active_subscription_for_retailer,
)


class PlanLimitExceededError(ValueError):
    """Raised when a retailer has reached a configured plan limit."""


def parse_plan_limits(
    plan: SubscriptionPlan,
) -> dict[str, Any]:
    if not plan.limits:
        return {}

    try:
        value = json.loads(plan.limits)
    except (TypeError, json.JSONDecodeError):
        return {}

    if not isinstance(value, dict):
        return {}

    return value


def get_retailer_subscription_and_plan(
    db: Session,
    retailer_id: uuid.UUID,
) -> tuple[Subscription, SubscriptionPlan]:
    subscription = get_active_subscription_for_retailer(
        db,
        retailer_id,
    )

    if subscription is None:
        raise ValueError(
            "Retailer does not have an active subscription."
        )

    plan = db.execute(
        select(SubscriptionPlan).where(
            SubscriptionPlan.id == subscription.plan_id
        )
    ).scalar_one_or_none()

    if plan is None:
        raise ValueError(
            "Retailer subscription plan not found."
        )

    if not plan.is_active:
        raise ValueError(
            "Retailer subscription plan is not active."
        )

    return subscription, plan


def get_limit_configuration(
    plan: SubscriptionPlan,
    resource: str,
) -> tuple[bool, Optional[int]]:
    limits = parse_plan_limits(plan)
    configuration = limits.get(resource)

    if not isinstance(configuration, dict):
        # A missing limit means the admin has not configured
        # a restriction for this resource. Treat it as unlimited.
        return True, None

    unlimited = bool(
        configuration.get("unlimited", False)
    )

    limit = configuration.get("limit")

    if limit is not None:
        try:
            limit = int(limit)
        except (TypeError, ValueError):
            limit = None

    return unlimited, limit


def get_product_usage(
    db: Session,
    retailer_id: uuid.UUID,
) -> int:
    statement = select(
        func.count(Product.id)
    ).where(
        Product.retailer_id == retailer_id,
        Product.status == "active",
    )

    return int(
        db.execute(statement).scalar_one()
    )


def check_product_limit(
    db: Session,
    retailer_id: uuid.UUID,
) -> None:
    subscription, plan = (
        get_retailer_subscription_and_plan(
            db,
            retailer_id,
        )
    )

    unlimited, limit = get_limit_configuration(
        plan,
        "products",
    )

    if unlimited:
        return

    if limit is None:
        raise ValueError(
            "Product limit is not configured for "
            "the retailer's subscription plan."
        )

    usage = get_product_usage(
        db,
        retailer_id,
    )

    if usage >= limit:
        raise PlanLimitExceededError(
            f"Product limit of {limit} has been reached "
            f"for the retailer's subscription plan."
        )


def get_invoice_usage(
    db: Session,
    retailer_id: uuid.UUID,
    subscription: Subscription,
) -> int:
    period_start = subscription.current_period_start
    period_end = subscription.current_period_end

    if period_start.tzinfo is None:
        period_start = period_start.replace(
            tzinfo=timezone.utc
        )

    if period_end.tzinfo is None:
        period_end = period_end.replace(
            tzinfo=timezone.utc
        )

    statement = select(
        func.count(Invoice.id)
    ).where(
        Invoice.retailer_id == retailer_id,
        Invoice.created_at >= period_start,
        Invoice.created_at < period_end,
    )

    return int(
        db.execute(statement).scalar_one()
    )


def check_invoice_limit(
    db: Session,
    retailer_id: uuid.UUID,
) -> None:
    subscription, plan = (
        get_retailer_subscription_and_plan(
            db,
            retailer_id,
        )
    )

    unlimited, limit = get_limit_configuration(
        plan,
        "invoices",
    )

    if unlimited:
        return

    if limit is None:
        raise ValueError(
            "Invoice limit is not configured for "
            "the retailer's subscription plan."
        )

    usage = get_invoice_usage(
        db,
        retailer_id,
        subscription,
    )

    if usage >= limit:
        raise PlanLimitExceededError(
            f"Invoice limit of {limit} has been reached "
            f"for the current subscription period."
        )
