from uuid import uuid4

from app.models.role import Role
from app.models.user import User
from app.models.access_control import user_roles
from app.services.auth_service import create_user_token


def create_customer_api_context(db):
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

    db.commit()

    token = create_user_token(user)

    return {
        "user": user,
        "token": token,
    }


def auth_headers(token):
    return {
        "Authorization": f"Bearer {token}",
    }


def test_create_customer_api(client, db):
    context = create_customer_api_context(db)

    response = client.post(
        "/customers",
        headers=auth_headers(context["token"]),
        json={
            "full_name": "API Test Customer",
            "phone_number": f"8{uuid4().hex[:9]}",
            "email": "customer@example.com",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["user_id"] == str(context["user"].id)
    assert data["full_name"] == "API Test Customer"
    assert data["email"] == "customer@example.com"
    assert data["status"] == "active"
    assert data["customer_id"].startswith("CUST-")


def test_get_my_customer_api(client, db):
    context = create_customer_api_context(db)

    create_response = client.post(
        "/customers",
        headers=auth_headers(context["token"]),
        json={
            "full_name": "API Test Customer",
            "phone_number": f"8{uuid4().hex[:9]}",
        },
    )

    assert create_response.status_code == 201

    response = client.get(
        "/customers/me",
        headers=auth_headers(context["token"]),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["user_id"] == str(context["user"].id)
    assert data["full_name"] == "API Test Customer"
    assert data["status"] == "active"


def test_get_my_customer_api_returns_404_when_profile_missing(
    client,
    db,
):
    context = create_customer_api_context(db)

    response = client.get(
        "/customers/me",
        headers=auth_headers(context["token"]),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Customer profile not found."


def test_create_customer_api_rejects_invalid_email(
    client,
    db,
):
    context = create_customer_api_context(db)

    response = client.post(
        "/customers",
        headers=auth_headers(context["token"]),
        json={
            "full_name": "API Test Customer",
            "phone_number": f"8{uuid4().hex[:9]}",
            "email": "not-an-email",
        },
    )

    assert response.status_code == 422


def test_create_customer_api_rejects_short_name(
    client,
    db,
):
    context = create_customer_api_context(db)

    response = client.post(
        "/customers",
        headers=auth_headers(context["token"]),
        json={
            "full_name": "A",
            "phone_number": f"8{uuid4().hex[:9]}",
        },
    )

    assert response.status_code == 422


def test_create_customer_api_rejects_short_phone(
    client,
    db,
):
    context = create_customer_api_context(db)

    response = client.post(
        "/customers",
        headers=auth_headers(context["token"]),
        json={
            "full_name": "API Test Customer",
            "phone_number": "123",
        },
    )

    assert response.status_code == 422
