import json
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from app.models.retailer import Retailer
from app.models.user import User
from app.models.subscription import Subscription
from app.models.subscription_plan import SubscriptionPlan
from app.services.plan_entitlement_service import (
    PlanFeatureNotAvailableError,
    parse_plan_features,
    require_retailer_feature,
    retailer_has_feature,
)


def create_retailer_with_plan(
    db,
    features,
    plan_active=True,
):
    user = User(
        phone_number=f"9{uuid4().hex[:9]}",
        status="active",
    )

    db.add(user)
    db.flush()

    retailer = Retailer(
        retailer_id=f"RET-ENT-{uuid4().hex[:8].upper()}",
        owner_user_id=user.id,
        business_name="Entitlement Test Retailer",
        phone_number=f"9{uuid4().hex[:9]}",
        status="active",
    )
    db.add(retailer)
    db.flush()

    plan = SubscriptionPlan(
        plan_id=f"test_entitlement_{uuid4().hex[:8]}",
        name="Entitlement Test Plan",
        description="Plan entitlement test plan",
        customer_type="retailer",
        billing_type="monthly",
        monthly_price=100,
        yearly_price=1200,
        per_bill_price=0,
        trial_days=0,
        features=json.dumps(features),
        limits=json.dumps({
            "invoices": {
                "unlimited": False,
                "limit": 100,
            },
            "employees": {
                "unlimited": False,
                "limit": 10,
            },
            "products": {
                "unlimited": False,
                "limit": 100,
            },
        }),
        is_active=plan_active,
    )
    db.add(plan)
    db.flush()

    now = datetime.now(timezone.utc)

    subscription = Subscription(
        subscription_id=f"SUB-ENT-{uuid4().hex[:8].upper()}",
        plan_id=plan.id,
        retailer_id=retailer.id,
        customer_id=None,
        status="active",
        started_at=now,
        current_period_start=now,
        current_period_end=now + timedelta(days=30),
        trial_ends_at=None,
        auto_renew=True,
    )
    db.add(subscription)
    db.commit()

    return retailer, plan, subscription


def test_parse_plan_features_returns_empty_list_when_missing():
    plan = SubscriptionPlan(
        plan_id=f"test_{uuid4().hex[:8]}",
        name="Test Plan",
        customer_type="retailer",
        billing_type="monthly",
        monthly_price=100,
        yearly_price=1200,
        per_bill_price=0,
        features=None,
        limits="{}",
        is_active=True,
    )

    assert parse_plan_features(plan) == []


def test_parse_plan_features_returns_configured_features():
    plan = SubscriptionPlan(
        plan_id=f"test_{uuid4().hex[:8]}",
        name="Test Plan",
        customer_type="retailer",
        billing_type="monthly",
        monthly_price=100,
        yearly_price=1200,
        per_bill_price=0,
        features=json.dumps([
            "billing",
            "inventory",
            "analytics",
        ]),
        limits="{}",
        is_active=True,
    )

    assert parse_plan_features(plan) == [
        "billing",
        "inventory",
        "analytics",
    ]


def test_retailer_has_feature_returns_true_when_enabled(db):
    retailer, _, _ = create_retailer_with_plan(
        db,
        ["billing", "inventory"],
    )

    assert retailer_has_feature(
        db,
        retailer.id,
        "billing",
    ) is True


def test_retailer_has_feature_returns_false_when_missing(db):
    retailer, _, _ = create_retailer_with_plan(
        db,
        ["billing"],
    )

    assert retailer_has_feature(
        db,
        retailer.id,
        "inventory",
    ) is False


def test_require_retailer_feature_rejects_missing_feature(db):
    retailer, _, _ = create_retailer_with_plan(
        db,
        ["billing"],
    )

    with pytest.raises(
        PlanFeatureNotAvailableError,
        match="inventory",
    ):
        require_retailer_feature(
            db,
            retailer.id,
            "inventory",
        )


def test_inactive_plan_is_rejected(db):
    retailer, _, _ = create_retailer_with_plan(
        db,
        ["billing"],
        plan_active=False,
    )

    with pytest.raises(
        ValueError,
        match="not active",
    ):
        retailer_has_feature(
            db,
            retailer.id,
            "billing",
        )


def test_no_active_subscription_is_rejected(db):
    retailer, plan, subscription = (
        create_retailer_with_plan(
            db,
            ["billing"],
        )
    )

    subscription.status = "cancelled"
    db.commit()

    with pytest.raises(
        ValueError,
        match="active subscription",
    ):
        retailer_has_feature(
            db,
            retailer.id,
            "billing",
        )
