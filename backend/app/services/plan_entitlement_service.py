import json
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.subscription import Subscription
from app.models.subscription_plan import SubscriptionPlan
from app.services.subscription_service import (
    get_active_subscription_for_retailer,
)


class PlanFeatureNotAvailableError(ValueError):
    """Raised when a retailer's plan does not include a feature."""


def parse_plan_features(
    plan: SubscriptionPlan,
) -> list[str]:
    if not plan.features:
        return []

    try:
        value = json.loads(plan.features)
    except (TypeError, json.JSONDecodeError):
        return []

    if not isinstance(value, list):
        return []

    return [
        str(feature).strip()
        for feature in value
        if str(feature).strip()
    ]


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


def retailer_has_feature(
    db: Session,
    retailer_id: uuid.UUID,
    feature: str,
) -> bool:
    _, plan = get_retailer_subscription_and_plan(
        db,
        retailer_id,
    )

    features = parse_plan_features(plan)

    return feature in features


def require_retailer_feature(
    db: Session,
    retailer_id: uuid.UUID,
    feature: str,
) -> None:
    if not retailer_has_feature(
        db,
        retailer_id,
        feature,
    ):
        raise PlanFeatureNotAvailableError(
            f"The '{feature}' feature is not available "
            f"on the retailer's current subscription plan."
        )
