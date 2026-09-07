import json
from decimal import Decimal
from uuid import uuid4

from app.models.access_control import user_roles
from app.models.role import Role
from app.models.subscription_plan import SubscriptionPlan
from app.models.user import User
from app.services.auth_service import create_user_token
from app.services.retailer_plan_service import ensure_retailer_plans


def auth_headers(token):
    return {
        "Authorization": f"Bearer {token}",
    }


def create_user_with_role(db, role_name):
    user = User(
        phone_number=f"7{uuid4().hex[:9]}",
        status="active",
    )
    db.add(user)
    db.flush()

    role = db.query(Role).filter(
        Role.name == role_name
    ).one()

    db.execute(
        user_roles.insert().values(
            user_id=user.id,
            role_id=role.id,
        )
    )

    db.commit()
    db.refresh(user)

    return user


def reset_retailer_plans(db):
    from app.models.subscription import Subscription
    from app.services.retailer_plan_service import (
        DEFAULT_RETAILER_PLANS,
    )

    canonical_plan_ids = {
        definition["plan_id"]
        for definition in DEFAULT_RETAILER_PLANS
    }

    retailer_plans = db.query(SubscriptionPlan).filter(
        SubscriptionPlan.customer_type == "retailer"
    ).all()

    plan_by_id = {
        plan.plan_id: plan
        for plan in retailer_plans
    }

    # Remove test subscriptions that point to temporary test plans.
    for plan in retailer_plans:
        if plan.plan_id not in canonical_plan_ids:
            db.query(Subscription).filter(
                Subscription.plan_id == plan.id
            ).delete(
                synchronize_session=False
            )

    # Remove temporary retailer plans after their subscriptions
    # have been removed.
    for plan in retailer_plans:
        if plan.plan_id not in canonical_plan_ids:
            db.delete(plan)

    db.flush()

    # Restore the three canonical plans to their default state.
    for definition in DEFAULT_RETAILER_PLANS:
        plan = plan_by_id.get(
            definition["plan_id"]
        )

        if plan is None:
            continue

        plan.name = definition["name"]
        plan.description = definition["description"]
        plan.billing_type = definition["billing_type"]
        plan.monthly_price = definition["monthly_price"]
        plan.yearly_price = definition["yearly_price"]
        plan.trial_days = definition["trial_days"]
        plan.features = json.dumps(
            definition["features"]
        )
        plan.limits = json.dumps(
            definition["limits"]
        )
        plan.is_active = True

    db.commit()

    ensure_retailer_plans(db)


def test_retailer_plans_require_authentication(client):
    response = client.get(
        "/admin/retailer-plans"
    )

    assert response.status_code == 401


def test_retailer_plans_require_super_admin(
    client,
    db,
):
    user = create_user_with_role(
        db,
        "retailer_owner",
    )

    token = create_user_token(user)

    response = client.get(
        "/admin/retailer-plans",
        headers=auth_headers(token),
    )

    assert response.status_code == 403
    assert response.json()["detail"] == (
        "Role 'super_admin' is required."
    )


def test_super_admin_gets_three_retailer_plans(
    client,
    db,
):
    reset_retailer_plans(db)

    user = create_user_with_role(
        db,
        "super_admin",
    )

    token = create_user_token(user)

    response = client.get(
        "/admin/retailer-plans",
        headers=auth_headers(token),
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 3

    assert {
        plan["plan_id"]
        for plan in data
    } == {
        "retailer_basic",
        "retailer_plus",
        "retailer_pro",
    }

    assert {
        plan["name"]
        for plan in data
    } == {
        "Basic",
        "Plus",
        "Pro",
    }


def test_retailer_plans_have_configurable_limits(
    client,
    db,
):
    reset_retailer_plans(db)

    user = create_user_with_role(
        db,
        "super_admin",
    )

    token = create_user_token(user)

    response = client.get(
        "/admin/retailer-plans",
        headers=auth_headers(token),
    )

    assert response.status_code == 200

    data = response.json()

    for plan in data:
        assert "limits" in plan
        assert plan["limits"] == {}

def test_super_admin_can_update_retailer_plan(
    client,
    db,
):
    reset_retailer_plans(db)

    user = create_user_with_role(
        db,
        "super_admin",
    )

    token = create_user_token(user)

    response = client.put(
        "/admin/retailer-plans/retailer_basic",
        headers=auth_headers(token),
        json={
            "name": "Basic",
            "description": "Basic retailer plan",
            "billing_type": "monthly",
            "monthly_price": "499.00",
            "yearly_price": "4999.00",
            "trial_days": 14,
            "features": [
                "billing",
                "inventory",
            ],
            "limits": {
                "invoices": {
                    "unlimited": False,
                    "limit": 500,
                },
                "employees": {
                    "unlimited": False,
                    "limit": 2,
                },
                "products": {
                    "unlimited": False,
                    "limit": 500,
                },
            },
            "is_active": True,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["plan_id"] == "retailer_basic"
    assert data["monthly_price"] == "499.00"
    assert data["yearly_price"] == "4999.00"
    assert data["trial_days"] == 14

    assert data["limits"]["invoices"] == {
        "unlimited": False,
        "limit": 500,
    }

    assert data["limits"]["employees"] == {
        "unlimited": False,
        "limit": 2,
    }


def test_unlimited_retailer_plan_limits_persist(
    client,
    db,
):
    reset_retailer_plans(db)

    user = create_user_with_role(
        db,
        "super_admin",
    )

    token = create_user_token(user)

    response = client.put(
        "/admin/retailer-plans/retailer_pro",
        headers=auth_headers(token),
        json={
            "name": "Pro",
            "description": "Unlimited Pro retailer plan",
            "billing_type": "yearly",
            "monthly_price": "1999.00",
            "yearly_price": "19999.00",
            "trial_days": 30,
            "features": [
                "billing",
                "inventory",
                "analytics",
                "warranty",
            ],
            "limits": {
                "invoices": {
                    "unlimited": True,
                    "limit": None,
                },
                "employees": {
                    "unlimited": True,
                    "limit": None,
                },
                "products": {
                    "unlimited": True,
                    "limit": None,
                },
            },
            "is_active": True,
        },
    )

    assert response.status_code == 200

    get_response = client.get(
        "/admin/retailer-plans",
        headers=auth_headers(token),
    )

    assert get_response.status_code == 200

    pro_plan = next(
        plan
        for plan in get_response.json()
        if plan["plan_id"] == "retailer_pro"
    )

    assert pro_plan["limits"]["invoices"] == {
        "unlimited": True,
        "limit": None,
    }

    assert pro_plan["limits"]["employees"] == {
        "unlimited": True,
        "limit": None,
    }

    assert pro_plan["limits"]["products"] == {
        "unlimited": True,
        "limit": None,
    }


def test_retailer_plan_update_for_unknown_plan_returns_404(
    client,
    db,
):
    reset_retailer_plans(db)

    user = create_user_with_role(
        db,
        "super_admin",
    )

    token = create_user_token(user)

    response = client.put(
        "/admin/retailer-plans/does_not_exist",
        headers=auth_headers(token),
        json={
            "name": "Unknown",
            "description": "Unknown plan",
            "billing_type": "monthly",
            "monthly_price": "100.00",
            "yearly_price": "1000.00",
            "trial_days": 0,
            "features": [],
            "limits": {
                "invoices": {
                    "unlimited": False,
                    "limit": 10,
                },
            },
            "is_active": True,
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == (
        "Retailer subscription plan not found."
    )
