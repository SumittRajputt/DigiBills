import uuid

from app.models.retailer import Retailer
from app.models.role import Role
from app.models.user import User
from app.models.access_control import user_roles
from app.services.auth_service import create_user_token



def create_supplier_api_context(db):
    user = User(
        phone_number=f"7{uuid.uuid4().hex[:9]}",
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
        retailer_id=f"RET-SUP-API-{uuid.uuid4().hex[:6].upper()}",
        owner_user_id=user.id,
        business_name="Supplier API Retailer",
        phone_number=user.phone_number,
        status="active",
    )
    db.add(retailer)
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


def test_create_supplier_api(client, db):
    context = create_supplier_api_context(db)

    response = client.post(
        "/suppliers",
        headers=auth_headers(context["token"]),
        json={
            "name": "API Test Supplier",
            "contact_person": "Test Contact",
            "phone_number": "9876543210",
            "email": "supplier@example.com",
            "address": "Delhi",
            "tax_identifier": "GST-TEST-001",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["retailer_id"] == str(
        context["retailer"].id
    )
    assert data["name"] == "API Test Supplier"
    assert data["contact_person"] == "Test Contact"
    assert data["phone_number"] == "9876543210"
    assert data["email"] == "supplier@example.com"
    assert data["address"] == "Delhi"
    assert data["tax_identifier"] == "GST-TEST-001"
    assert data["is_active"] is True
    assert data["supplier_id"].startswith("SUP-")


def test_create_supplier_api_with_optional_fields_omitted(
    client,
    db,
):
    context = create_supplier_api_context(db)

    response = client.post(
        "/suppliers",
        headers=auth_headers(context["token"]),
        json={
            "name": "Minimal Supplier",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["name"] == "Minimal Supplier"
    assert data["contact_person"] is None
    assert data["phone_number"] is None
    assert data["email"] is None
    assert data["address"] is None
    assert data["tax_identifier"] is None
    assert data["is_active"] is True


def test_list_suppliers_api(client, db):
    context = create_supplier_api_context(db)

    for name in [
        "Supplier One",
        "Supplier Two",
    ]:
        response = client.post(
            "/suppliers",
            headers=auth_headers(context["token"]),
            json={
                "name": name,
            },
        )
        assert response.status_code == 201

    response = client.get(
        "/suppliers",
        headers=auth_headers(context["token"]),
    )

    assert response.status_code == 200

    data = response.json()

    names = {supplier["name"] for supplier in data}

    assert "Supplier One" in names
    assert "Supplier Two" in names


def test_get_supplier_api(client, db):
    context = create_supplier_api_context(db)

    create_response = client.post(
        "/suppliers",
        headers=auth_headers(context["token"]),
        json={
            "name": "Get Supplier",
        },
    )

    assert create_response.status_code == 201

    supplier = create_response.json()

    response = client.get(
        f"/suppliers/{supplier['supplier_id']}",
        headers=auth_headers(context["token"]),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["supplier_id"] == supplier["supplier_id"]
    assert data["name"] == "Get Supplier"


def test_get_supplier_api_returns_404_for_unknown_supplier(
    client,
    db,
):
    context = create_supplier_api_context(db)

    response = client.get(
        "/suppliers/SUP-NOT-FOUND",
        headers=auth_headers(context["token"]),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Supplier not found."


def test_create_supplier_api_rejects_invalid_email(
    client,
    db,
):
    context = create_supplier_api_context(db)

    response = client.post(
        "/suppliers",
        headers=auth_headers(context["token"]),
        json={
            "name": "Invalid Email Supplier",
            "email": "not-an-email",
        },
    )

    assert response.status_code == 422


def test_create_supplier_api_rejects_empty_name(
    client,
    db,
):
    context = create_supplier_api_context(db)

    response = client.post(
        "/suppliers",
        headers=auth_headers(context["token"]),
        json={
            "name": "",
        },
    )

    assert response.status_code == 422


def test_create_supplier_api_requires_authentication(
    client,
):
    response = client.post(
        "/suppliers",
        json={
            "name": "Unauthorized Supplier",
        },
    )

    assert response.status_code in (401, 403)


def test_list_suppliers_api_requires_authentication(
    client,
):
    response = client.get("/suppliers")

    assert response.status_code in (401, 403)


def test_get_supplier_api_requires_authentication(
    client,
):
    response = client.get(
        "/suppliers/SUP-NOT-FOUND"
    )

    assert response.status_code in (401, 403)
