from uuid import uuid4

from app.models.retailer import Retailer
from app.models.role import Role
from app.models.user import User
from app.models.access_control import user_roles
from app.services.auth_service import create_user_token


def create_inventory_location_api_context(db):
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
        retailer_id=f"RET-LOC-API-{uuid4().hex[:6].upper()}",
        owner_user_id=user.id,
        business_name="Inventory Location API Retailer",
        phone_number=user.phone_number,
        status="active",
    )
    db.add(retailer)
    db.flush()

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


def test_create_inventory_location_api(client, db):
    context = create_inventory_location_api_context(db)

    response = client.post(
        "/inventory-locations",
        headers=auth_headers(context["token"]),
        json={
            "name": "Main Store",
            "location_type": "store",
            "address": "Delhi",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["retailer_id"] == str(context["retailer"].id)
    assert data["name"] == "Main Store"
    assert data["location_type"] == "store"
    assert data["address"] == "Delhi"
    assert data["is_active"] is True
    assert data["id"]


def test_create_inventory_location_api_without_address(
    client,
    db,
):
    context = create_inventory_location_api_context(db)

    response = client.post(
        "/inventory-locations",
        headers=auth_headers(context["token"]),
        json={
            "name": "Warehouse",
            "location_type": "warehouse",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["name"] == "Warehouse"
    assert data["location_type"] == "warehouse"
    assert data["address"] is None


def test_create_inventory_location_api_rejects_duplicate_name(
    client,
    db,
):
    context = create_inventory_location_api_context(db)

    payload = {
        "name": "Main Store",
        "location_type": "store",
        "address": "Delhi",
    }

    first = client.post(
        "/inventory-locations",
        headers=auth_headers(context["token"]),
        json=payload,
    )

    assert first.status_code == 201

    second = client.post(
        "/inventory-locations",
        headers=auth_headers(context["token"]),
        json=payload,
    )

    assert second.status_code == 409


def test_create_inventory_location_api_rejects_short_name(
    client,
    db,
):
    context = create_inventory_location_api_context(db)

    response = client.post(
        "/inventory-locations",
        headers=auth_headers(context["token"]),
        json={
            "name": "A",
            "location_type": "store",
        },
    )

    assert response.status_code == 422


def test_create_inventory_location_api_rejects_short_location_type(
    client,
    db,
):
    context = create_inventory_location_api_context(db)

    response = client.post(
        "/inventory-locations",
        headers=auth_headers(context["token"]),
        json={
            "name": "Main Store",
            "location_type": "A",
        },
    )

    assert response.status_code == 422


def test_create_inventory_location_api_rejects_missing_name(
    client,
    db,
):
    context = create_inventory_location_api_context(db)

    response = client.post(
        "/inventory-locations",
        headers=auth_headers(context["token"]),
        json={
            "location_type": "store",
        },
    )

    assert response.status_code == 422


def test_create_inventory_location_api_rejects_missing_location_type(
    client,
    db,
):
    context = create_inventory_location_api_context(db)

    response = client.post(
        "/inventory-locations",
        headers=auth_headers(context["token"]),
        json={
            "name": "Main Store",
        },
    )

    assert response.status_code == 422


def test_create_inventory_location_api_rejects_inactive_retailer(
    client,
    db,
):
    context = create_inventory_location_api_context(db)

    context["retailer"].status = "inactive"
    db.commit()

    response = client.post(
        "/inventory-locations",
        headers=auth_headers(context["token"]),
        json={
            "name": "Main Store",
            "location_type": "store",
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "Retailer is not active."


def test_create_inventory_location_api_rejects_unauthenticated(
    client,
    db,
):
    response = client.post(
        "/inventory-locations",
        json={
            "name": "Main Store",
            "location_type": "store",
        },
    )

    assert response.status_code == 401


def test_create_inventory_location_api_does_not_leak_other_retailer(
    client,
    db,
):
    context = create_inventory_location_api_context(db)

    other_user = User(
        phone_number=f"8{uuid4().hex[:9]}",
        status="active",
    )
    db.add(other_user)
    db.flush()

    other_retailer = Retailer(
        retailer_id=f"RET-OTHER-{uuid4().hex[:8].upper()}",
        owner_user_id=other_user.id,
        business_name="Other Retailer",
        phone_number=other_user.phone_number,
        status="active",
    )
    db.add(other_retailer)
    db.commit()

    response = client.post(
        "/inventory-locations",
        headers=auth_headers(context["token"]),
        json={
            "name": "Other Store",
            "location_type": "store",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["retailer_id"] == str(context["retailer"].id)
    assert data["retailer_id"] != str(other_retailer.id)
