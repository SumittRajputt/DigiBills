from uuid import uuid4

from app.models.access_control import user_roles
from app.models.role import Role
from app.models.user import User
from app.services.auth_service import create_user_token
from app.services.auth_service import register_user


def auth_headers(token):
    return {
        "Authorization": f"Bearer {token}",
    }


def test_register_api(client):
    phone = f"7{uuid4().hex[:9]}"

    response = client.post(
        "/auth/register",
        json={
            "phone_number": phone,
            "email": f"{uuid4().hex[:8]}@example.com",
            "password": "TestPassword123",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["id"]
    assert data["phone_number"] == phone
    assert data["status"] == "active"
    assert data["is_phone_verified"] is False


def test_register_api_rejects_duplicate_phone(client, db):
    phone = f"7{uuid4().hex[:9]}"

    register_user(
        db=db,
        phone_number=phone,
        email=None,
        password="TestPassword123",
    )

    response = client.post(
        "/auth/register",
        json={
            "phone_number": phone,
            "password": "AnotherPassword123",
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"] == (
        "A user with this phone number already exists."
    )


def test_register_api_rejects_duplicate_email(client, db):
    phone1 = f"7{uuid4().hex[:9]}"
    phone2 = f"8{uuid4().hex[:9]}"
    email = f"{uuid4().hex[:8]}@example.com"

    register_user(
        db=db,
        phone_number=phone1,
        email=email,
        password="TestPassword123",
    )

    response = client.post(
        "/auth/register",
        json={
            "phone_number": phone2,
            "email": email,
            "password": "AnotherPassword123",
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"] == (
        "A user with this email already exists."
    )


def test_register_api_rejects_invalid_password(client):
    response = client.post(
        "/auth/register",
        json={
            "phone_number": f"7{uuid4().hex[:9]}",
            "password": "short",
        },
    )

    assert response.status_code == 422


def test_login_api(client, db):
    phone = f"7{uuid4().hex[:9]}"

    register_user(
        db=db,
        phone_number=phone,
        email=None,
        password="TestPassword123",
    )

    response = client.post(
        "/auth/login",
        json={
            "phone_number": phone,
            "password": "TestPassword123",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["access_token"]
    assert data["token_type"] == "bearer"


def test_login_api_rejects_wrong_password(client, db):
    phone = f"7{uuid4().hex[:9]}"

    register_user(
        db=db,
        phone_number=phone,
        email=None,
        password="TestPassword123",
    )

    response = client.post(
        "/auth/login",
        json={
            "phone_number": phone,
            "password": "WrongPassword123",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == (
        "Invalid phone number or password."
    )


def test_login_api_rejects_unknown_user(client):
    response = client.post(
        "/auth/login",
        json={
            "phone_number": f"7{uuid4().hex[:9]}",
            "password": "TestPassword123",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == (
        "Invalid phone number or password."
    )


def test_login_api_rejects_inactive_user(client, db):
    phone = f"7{uuid4().hex[:9]}"

    user = register_user(
        db=db,
        phone_number=phone,
        email=None,
        password="TestPassword123",
    )

    user.status = "inactive"
    db.commit()

    response = client.post(
        "/auth/login",
        json={
            "phone_number": phone,
            "password": "TestPassword123",
        },
    )

    assert response.status_code == 401


def test_get_me_api(client, db):
    user = User(
        phone_number=f"7{uuid4().hex[:9]}",
        status="active",
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_user_token(user)

    response = client.get(
        "/auth/me",
        headers=auth_headers(token),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == str(user.id)
    assert data["phone_number"] == user.phone_number
    assert data["status"] == "active"
    assert data["is_phone_verified"] is False


def test_get_me_api_requires_authentication(client):
    response = client.get("/auth/me")

    assert response.status_code == 401


def test_authorization_test_api_with_permission(client, db):
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
    db.commit()
    db.refresh(user)

    token = create_user_token(user)

    response = client.get(
        "/auth/authorization-test",
        headers=auth_headers(token),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "authorized"
    assert data["user_id"] == str(user.id)
    assert data["phone_number"] == user.phone_number
    assert data["permission"] == "retailer.manage"


def test_authorization_test_api_requires_authentication(client):
    response = client.get("/auth/authorization-test")

    assert response.status_code == 401
