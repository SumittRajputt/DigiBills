from uuid import uuid4

from app.models.access_control import user_roles
from app.models.retailer import Retailer
from app.models.role import Role
from app.models.user import User
from app.services.auth_service import create_user_token


def create_retailer_api_context(db):
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

    return {
        "user": user,
        "token": create_user_token(user),
    }


def auth_headers(token):
    return {
        "Authorization": f"Bearer {token}",
    }


def test_create_retailer_api(client, db):
    context = create_retailer_api_context(db)

    response = client.post(
        "/retailers",
        headers=auth_headers(context["token"]),
        json={
            "business_name": "API Test Retailer",
            "business_type": "Electronics",
            "phone_number": "9876543210",
            "email": "retailer@example.com",
            "address": "Delhi",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["owner_user_id"] == str(context["user"].id)
    assert data["business_name"] == "API Test Retailer"
    assert data["business_type"] == "Electronics"
    assert data["phone_number"] == "9876543210"
    assert data["email"] == "retailer@example.com"
    assert data["address"] == "Delhi"
    assert data["status"] == "pending"
    assert data["approved_at"] is None
    assert data["approved_by"] is None
    assert data["rejection_reason"] is None
    assert data["retailer_id"].startswith("RET-")


def test_create_retailer_api_with_optional_fields_omitted(
    client,
    db,
):
    context = create_retailer_api_context(db)

    response = client.post(
        "/retailers",
        headers=auth_headers(context["token"]),
        json={
            "business_name": "Minimal Retailer",
            "business_type": "General Store",
            "phone_number": "9876543210",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["business_name"] == "Minimal Retailer"
    assert data["business_type"] == "General Store"
    assert data["email"] is None
    assert data["address"] is None
    assert data["status"] == "pending"


def test_get_my_retailer_api(client, db):
    context = create_retailer_api_context(db)

    create_response = client.post(
        "/retailers",
        headers=auth_headers(context["token"]),
        json={
            "business_name": "My Retailer",
            "business_type": "Retail",
            "phone_number": "9876543210",
        },
    )

    assert create_response.status_code == 201

    response = client.get(
        "/retailers/me",
        headers=auth_headers(context["token"]),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["owner_user_id"] == str(context["user"].id)
    assert data["business_name"] == "My Retailer"
    assert data["status"] == "pending"


def test_get_my_retailer_api_returns_404_when_missing(
    client,
    db,
):
    context = create_retailer_api_context(db)

    response = client.get(
        "/retailers/me",
        headers=auth_headers(context["token"]),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == (
        "Retailer not found for this user."
    )


def test_create_retailer_api_rejects_duplicate_owner(
    client,
    db,
):
    context = create_retailer_api_context(db)

    payload = {
        "business_name": "First Retailer",
        "business_type": "Retail",
        "phone_number": "9876543210",
    }

    first = client.post(
        "/retailers",
        headers=auth_headers(context["token"]),
        json=payload,
    )

    assert first.status_code == 201

    second = client.post(
        "/retailers",
        headers=auth_headers(context["token"]),
        json={
            **payload,
            "business_name": "Second Retailer",
        },
    )

    assert second.status_code == 409
    assert second.json()["detail"] == (
        "This user already owns a retailer."
    )


def test_create_retailer_api_rejects_invalid_email(
    client,
    db,
):
    context = create_retailer_api_context(db)

    response = client.post(
        "/retailers",
        headers=auth_headers(context["token"]),
        json={
            "business_name": "Invalid Email Retailer",
            "business_type": "Retail",
            "phone_number": "9876543210",
            "email": "not-an-email",
        },
    )

    assert response.status_code == 422


def test_create_retailer_api_rejects_short_business_name(
    client,
    db,
):
    context = create_retailer_api_context(db)

    response = client.post(
        "/retailers",
        headers=auth_headers(context["token"]),
        json={
            "business_name": "A",
            "business_type": "Retail",
            "phone_number": "9876543210",
        },
    )

    assert response.status_code == 422


def test_create_retailer_api_rejects_short_business_type(
    client,
    db,
):
    context = create_retailer_api_context(db)

    response = client.post(
        "/retailers",
        headers=auth_headers(context["token"]),
        json={
            "business_name": "Valid Retailer",
            "business_type": "A",
            "phone_number": "9876543210",
        },
    )

    assert response.status_code == 422


def test_create_retailer_api_rejects_short_phone(
    client,
    db,
):
    context = create_retailer_api_context(db)

    response = client.post(
        "/retailers",
        headers=auth_headers(context["token"]),
        json={
            "business_name": "Valid Retailer",
            "business_type": "Retail",
            "phone_number": "123",
        },
    )

    assert response.status_code == 422


def test_approve_retailer_api(client, db):
    context = create_retailer_api_context(db)

    create_response = client.post(
        "/retailers",
        headers=auth_headers(context["token"]),
        json={
            "business_name": "Pending Retailer",
            "business_type": "Retail",
            "phone_number": "9876543210",
        },
    )

    assert create_response.status_code == 201

    retailer_id = create_response.json()["retailer_id"]

    response = client.post(
        f"/retailers/{retailer_id}/approve",
        headers=auth_headers(context["token"]),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "active"
    assert data["approved_at"] is not None
    assert data["approved_by"] == str(context["user"].id)
    assert data["rejection_reason"] is None


def test_approve_retailer_api_rejects_already_active(
    client,
    db,
):
    context = create_retailer_api_context(db)

    create_response = client.post(
        "/retailers",
        headers=auth_headers(context["token"]),
        json={
            "business_name": "Active Retailer",
            "business_type": "Retail",
            "phone_number": "9876543210",
        },
    )

    retailer_id = create_response.json()["retailer_id"]

    first = client.post(
        f"/retailers/{retailer_id}/approve",
        headers=auth_headers(context["token"]),
    )

    assert first.status_code == 200

    second = client.post(
        f"/retailers/{retailer_id}/approve",
        headers=auth_headers(context["token"]),
    )

    assert second.status_code == 409
    assert second.json()["detail"] == (
        "Retailer is already active."
    )


def test_approve_retailer_api_returns_404_for_unknown_retailer(
    client,
    db,
):
    context = create_retailer_api_context(db)

    response = client.post(
        "/retailers/RET-NOT-FOUND/approve",
        headers=auth_headers(context["token"]),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Retailer not found."


def test_reject_retailer_api(client, db):
    context = create_retailer_api_context(db)

    create_response = client.post(
        "/retailers",
        headers=auth_headers(context["token"]),
        json={
            "business_name": "Reject Retailer",
            "business_type": "Retail",
            "phone_number": "9876543210",
        },
    )

    assert create_response.status_code == 201

    retailer_id = create_response.json()["retailer_id"]

    response = client.post(
        f"/retailers/{retailer_id}/reject",
        headers=auth_headers(context["token"]),
        json={
            "rejection_reason": "Documents are incomplete.",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "rejected"
    assert data["approved_at"] is None
    assert data["approved_by"] == str(context["user"].id)
    assert data["rejection_reason"] == (
        "Documents are incomplete."
    )


def test_reject_retailer_api_rejects_short_reason(
    client,
    db,
):
    context = create_retailer_api_context(db)

    create_response = client.post(
        "/retailers",
        headers=auth_headers(context["token"]),
        json={
            "business_name": "Reject Retailer",
            "business_type": "Retail",
            "phone_number": "9876543210",
        },
    )

    retailer_id = create_response.json()["retailer_id"]

    response = client.post(
        f"/retailers/{retailer_id}/reject",
        headers=auth_headers(context["token"]),
        json={
            "rejection_reason": "No",
        },
    )

    assert response.status_code == 422


def test_reject_retailer_api_returns_404_for_unknown_retailer(
    client,
    db,
):
    context = create_retailer_api_context(db)

    response = client.post(
        "/retailers/RET-NOT-FOUND/reject",
        headers=auth_headers(context["token"]),
        json={
            "rejection_reason": "Documents are incomplete.",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Retailer not found."


def test_reject_retailer_api_rejects_already_rejected(
    client,
    db,
):
    context = create_retailer_api_context(db)

    create_response = client.post(
        "/retailers",
        headers=auth_headers(context["token"]),
        json={
            "business_name": "Rejected Retailer",
            "business_type": "Retail",
            "phone_number": "9876543210",
        },
    )

    retailer_id = create_response.json()["retailer_id"]

    first = client.post(
        f"/retailers/{retailer_id}/reject",
        headers=auth_headers(context["token"]),
        json={
            "rejection_reason": "Documents are incomplete.",
        },
    )

    assert first.status_code == 200

    second = client.post(
        f"/retailers/{retailer_id}/reject",
        headers=auth_headers(context["token"]),
        json={
            "rejection_reason": "Another reason.",
        },
    )

    assert second.status_code == 409
    assert second.json()["detail"] == (
        "Retailer is already rejected."
    )


def test_approve_retailer_api_rejects_rejected_retailer(
    client,
    db,
):
    context = create_retailer_api_context(db)

    create_response = client.post(
        "/retailers",
        headers=auth_headers(context["token"]),
        json={
            "business_name": "Rejected Retailer",
            "business_type": "Retail",
            "phone_number": "9876543210",
        },
    )

    retailer_id = create_response.json()["retailer_id"]

    reject_response = client.post(
        f"/retailers/{retailer_id}/reject",
        headers=auth_headers(context["token"]),
        json={
            "rejection_reason": "Documents are incomplete.",
        },
    )

    assert reject_response.status_code == 200

    response = client.post(
        f"/retailers/{retailer_id}/approve",
        headers=auth_headers(context["token"]),
    )

    assert response.status_code == 409
    assert response.json()["detail"] == (
        "A rejected retailer cannot be approved directly."
    )


def test_create_retailer_api_requires_authentication(client):
    response = client.post(
        "/retailers",
        json={
            "business_name": "Unauthorized Retailer",
            "business_type": "Retail",
            "phone_number": "9876543210",
        },
    )

    assert response.status_code in (401, 403)
