from uuid import uuid4

from app.models.access_control import user_roles
from app.models.retailer import Retailer
from app.models.subscription import Subscription
from app.models.subscription_plan import SubscriptionPlan
from app.services.retailer_plan_service import ensure_retailer_plans
from app.models.role import Role
from app.models.user import User
from app.services.auth_service import create_user_token


def create_product_api_context(db):
    user = User(
        phone_number=f"7{uuid4().hex[:9]}",
        status="active",
    )
    db.add(user)
    db.flush()

    role = db.query(Role).filter(
        Role.name == "retailer_owner"
    ).one()

    db.execute(
        user_roles.insert().values(
            user_id=user.id,
            role_id=role.id,
        )
    )
    db.flush()

    retailer = Retailer(
        retailer_id=f"RET-PROD-API-{uuid4().hex[:6].upper()}",
        owner_user_id=user.id,
        business_name="Product API Retailer",
        phone_number=user.phone_number,
        status="active",
    )
    db.add(retailer)
    db.flush()

    ensure_retailer_plans(db)

    plan = db.query(SubscriptionPlan).filter(
        SubscriptionPlan.plan_id == "retailer_pro"
    ).one()

    subscription = Subscription(
        subscription_id=f"SUB-PROD-{uuid4().hex[:8].upper()}",
        plan_id=plan.id,
        retailer_id=retailer.id,
        customer_id=None,
        status="active",
        started_at=plan.created_at,
        current_period_start=plan.created_at,
        current_period_end=plan.created_at,
        trial_ends_at=None,
        auto_renew=True,
    )

    db.add(subscription)
    db.commit()

    return {
        "user": user,
        "retailer": retailer,
        "token": create_user_token(user),
    }


def auth_headers(token):
    return {
        "Authorization": f"Bearer {token}",
    }


def test_create_product_api(client, db):
    context = create_product_api_context(db)

    response = client.post(
        "/products",
        headers=auth_headers(context["token"]),
        json={
            "product_code": f"PROD-API-{uuid4().hex[:8].upper()}",
            "name": "API Test Product",
            "brand": "Test Brand",
            "category": "Electronics",
            "description": "Product API test",
            "is_transferable": True,
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["product_code"].startswith("PROD-API-")
    assert data["name"] == "API Test Product"
    assert data["brand"] == "Test Brand"
    assert data["category"] == "Electronics"
    assert data["description"] == "Product API test"
    assert data["is_transferable"] is True
    assert data["status"] == "active"
    assert data["id"]


def test_create_product_api_with_optional_fields_omitted(
    client,
    db,
):
    context = create_product_api_context(db)

    response = client.post(
        "/products",
        headers=auth_headers(context["token"]),
        json={
            "product_code": f"PROD-API-{uuid4().hex[:8].upper()}",
            "name": "Minimal Product",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["product_code"].startswith("PROD-API-")
    assert data["name"] == "Minimal Product"
    assert data["brand"] is None
    assert data["category"] is None
    assert data["description"] is None
    assert data["is_transferable"] is True


def test_create_product_api_can_disable_transferability(
    client,
    db,
):
    context = create_product_api_context(db)

    response = client.post(
        "/products",
        headers=auth_headers(context["token"]),
        json={
            "product_code": f"PROD-API-{uuid4().hex[:8].upper()}",
            "name": "Non Transferable Product",
            "is_transferable": False,
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["is_transferable"] is False


def test_create_product_api_rejects_duplicate_product_code(
    client,
    db,
):
    context = create_product_api_context(db)

    payload = {
        "product_code": f"PROD-DUPLICATE-{uuid4().hex[:8].upper()}",
        "name": "Duplicate Product",
    }

    first = client.post(
        "/products",
        headers=auth_headers(context["token"]),
        json=payload,
    )

    assert first.status_code == 201

    second = client.post(
        "/products",
        headers=auth_headers(context["token"]),
        json={
            "product_code": payload["product_code"],
            "name": "Another Product",
        },
    )

    assert second.status_code == 409


def test_create_product_api_rejects_missing_product_code(
    client,
    db,
):
    context = create_product_api_context(db)

    response = client.post(
        "/products",
        headers=auth_headers(context["token"]),
        json={
            "name": "Product Without Code",
        },
    )

    assert response.status_code == 422


def test_create_product_api_rejects_empty_product_code(
    client,
    db,
):
    context = create_product_api_context(db)

    response = client.post(
        "/products",
        headers=auth_headers(context["token"]),
        json={
            "product_code": "",
            "name": "Product",
        },
    )

    assert response.status_code == 422


def test_create_product_api_rejects_short_name(
    client,
    db,
):
    context = create_product_api_context(db)

    response = client.post(
        "/products",
        headers=auth_headers(context["token"]),
        json={
            "product_code": "PROD-API-004",
            "name": "A",
        },
    )

    assert response.status_code == 422


def test_get_product_api(client, db):
    context = create_product_api_context(db)

    create_response = client.post(
        "/products",
        headers=auth_headers(context["token"]),
        json={
            "product_code": f"PROD-GET-{uuid4().hex[:8].upper()}",
            "name": "Get Product",
            "brand": "Brand",
            "category": "Category",
        },
    )

    assert create_response.status_code == 201

    product_code = create_response.json()["product_code"]

    response = client.get(
        f"/products/{product_code}",
        headers=auth_headers(context["token"]),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["product_code"] == product_code
    assert data["name"] == "Get Product"
    assert data["brand"] == "Brand"
    assert data["category"] == "Category"
    assert data["status"] == "active"


def test_get_product_api_returns_404_for_unknown_product(
    client,
    db,
):
    context = create_product_api_context(db)

    response = client.get(
        "/products/PROD-DOES-NOT-EXIST",
        headers=auth_headers(context["token"]),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Product not found."


def test_product_api_requires_authentication(
    client,
    db,
):
    response = client.get(
        "/products/PROD-DOES-NOT-EXIST",
    )

    assert response.status_code == 401


def test_create_product_api_requires_authentication(
    client,
    db,
):
    response = client.post(
        "/products",
        json={
            "product_code": "PROD-NO-AUTH",
            "name": "Unauthorized Product",
        },
    )

    assert response.status_code == 401

def test_products_are_isolated_between_retailers(client, db):
    retailer_a = create_product_api_context(db)
    retailer_b = create_product_api_context(db)

    product_a_code = f"PROD-A-{uuid4().hex[:8].upper()}"
    product_b_code = f"PROD-B-{uuid4().hex[:8].upper()}"

    response_a = client.post(
        "/products",
        headers=auth_headers(retailer_a["token"]),
        json={
            "product_code": product_a_code,
            "name": "Retailer A Product",
        },
    )

    response_b = client.post(
        "/products",
        headers=auth_headers(retailer_b["token"]),
        json={
            "product_code": product_b_code,
            "name": "Retailer B Product",
        },
    )

    assert response_a.status_code == 201
    assert response_b.status_code == 201

    list_response = client.get(
        "/products",
        headers=auth_headers(retailer_a["token"]),
    )

    assert list_response.status_code == 200

    products = list_response.json()
    product_codes = {
        product["product_code"]
        for product in products
    }

    assert product_a_code in product_codes
    assert product_b_code not in product_codes

    cross_retailer_response = client.get(
        f"/products/{product_b_code}",
        headers=auth_headers(retailer_a["token"]),
    )

    assert cross_retailer_response.status_code == 404



def test_create_product_api_enforces_configured_product_limit(
    client,
    db,
):
    context = create_product_api_context(db)

    plan = db.query(SubscriptionPlan).filter(
        SubscriptionPlan.plan_id == "retailer_pro"
    ).one()

    plan.limits = (
        '{"products":{"unlimited":false,"limit":1}}'
    )
    db.commit()

    first_response = client.post(
        "/products",
        headers=auth_headers(context["token"]),
        json={
            "product_code": f"PROD-LIMIT-1-{uuid4().hex[:8].upper()}",
            "name": "First Limited Product",
        },
    )

    assert first_response.status_code == 201

    second_response = client.post(
        "/products",
        headers=auth_headers(context["token"]),
        json={
            "product_code": f"PROD-LIMIT-2-{uuid4().hex[:8].upper()}",
            "name": "Second Limited Product",
        },
    )

    assert second_response.status_code == 403
    assert "Product limit of 1 has been reached" in (
        second_response.json()["detail"]
    )
