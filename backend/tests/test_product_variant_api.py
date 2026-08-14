import uuid
from decimal import Decimal

from app.models.access_control import user_roles
from app.models.product import Product
from app.models.role import Role
from app.models.user import User
from app.services.auth_service import create_user_token


def create_product_variant_api_context(db):
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

    product = Product(
        product_code=f"PROD-VAR-API-{uuid.uuid4().hex[:8].upper()}",
        name="Variant API Product",
        brand="Test Brand",
        category="Electronics",
        description="Product variant API test",
        is_transferable=True,
        status="active",
    )
    db.add(product)
    db.commit()

    return {
        "user": user,
        "product": product,
        "token": create_user_token(user),
    }


def auth_headers(token):
    return {
        "Authorization": f"Bearer {token}",
    }


def test_create_product_variant_api(client, db):
    context = create_product_variant_api_context(db)

    sku = f"SKU-API-{uuid.uuid4().hex[:8].upper()}"
    barcode = f"BAR-{uuid.uuid4().hex[:10].upper()}"

    response = client.post(
        "/product-variants",
        headers=auth_headers(context["token"]),
        json={
            "product_code": context["product"].product_code,
            "sku": sku,
            "barcode": barcode,
            "variant_name": "Standard Variant",
            "selling_price": "1999.99",
            "purchase_cost": "1200.00",
            "tax_rate": "18.00",
            "track_inventory": True,
            "requires_serial_number": False,
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["product_id"] == str(context["product"].id)
    assert data["sku"] == sku
    assert data["barcode"] == barcode
    assert data["variant_name"] == "Standard Variant"
    assert Decimal(data["selling_price"]) == Decimal("1999.99")
    assert Decimal(data["purchase_cost"]) == Decimal("1200.00")
    assert Decimal(data["tax_rate"]) == Decimal("18.00")
    assert data["track_inventory"] is True
    assert data["requires_serial_number"] is False
    assert data["status"] == "active"
    assert data["id"]


def test_create_product_variant_api_with_optional_fields_omitted(
    client,
    db,
):
    context = create_product_variant_api_context(db)

    sku = f"SKU-MIN-{uuid.uuid4().hex[:8].upper()}"

    response = client.post(
        "/product-variants",
        headers=auth_headers(context["token"]),
        json={
            "product_code": context["product"].product_code,
            "sku": sku,
            "variant_name": "Minimal Variant",
            "selling_price": "999.00",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["sku"] == sku
    assert data["barcode"] is None
    assert data["purchase_cost"] is None
    assert Decimal(data["tax_rate"]) == Decimal("0.00")
    assert data["track_inventory"] is True
    assert data["requires_serial_number"] is False
    assert data["status"] == "active"


def test_create_product_variant_api_with_serial_tracking(
    client,
    db,
):
    context = create_product_variant_api_context(db)

    response = client.post(
        "/product-variants",
        headers=auth_headers(context["token"]),
        json={
            "product_code": context["product"].product_code,
            "sku": f"SKU-SERIAL-{uuid.uuid4().hex[:8].upper()}",
            "variant_name": "Serialized Variant",
            "selling_price": "4999.00",
            "purchase_cost": "3500.00",
            "requires_serial_number": True,
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["requires_serial_number"] is True
    assert data["track_inventory"] is True


def test_create_product_variant_api_can_disable_inventory_tracking(
    client,
    db,
):
    context = create_product_variant_api_context(db)

    response = client.post(
        "/product-variants",
        headers=auth_headers(context["token"]),
        json={
            "product_code": context["product"].product_code,
            "sku": f"SKU-NO-INV-{uuid.uuid4().hex[:8].upper()}",
            "variant_name": "Non Inventory Variant",
            "selling_price": "799.00",
            "track_inventory": False,
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["track_inventory"] is False


def test_create_product_variant_api_rejects_missing_product(
    client,
    db,
):
    context = create_product_variant_api_context(db)

    response = client.post(
        "/product-variants",
        headers=auth_headers(context["token"]),
        json={
            "product_code": "PROD-DOES-NOT-EXIST",
            "sku": f"SKU-MISSING-{uuid.uuid4().hex[:8].upper()}",
            "variant_name": "Missing Product Variant",
            "selling_price": "1000.00",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Product not found."


def test_create_product_variant_api_rejects_duplicate_sku(
    client,
    db,
):
    context = create_product_variant_api_context(db)

    sku = f"SKU-DUP-{uuid.uuid4().hex[:8].upper()}"

    payload = {
        "product_code": context["product"].product_code,
        "sku": sku,
        "variant_name": "Duplicate SKU Variant",
        "selling_price": "1000.00",
    }

    first = client.post(
        "/product-variants",
        headers=auth_headers(context["token"]),
        json=payload,
    )

    assert first.status_code == 201

    second = client.post(
        "/product-variants",
        headers=auth_headers(context["token"]),
        json={
            **payload,
            "variant_name": "Another Variant",
        },
    )

    assert second.status_code == 409
    assert second.json()["detail"] == (
        "A variant with this SKU already exists."
    )


def test_create_product_variant_api_rejects_duplicate_barcode(
    client,
    db,
):
    context = create_product_variant_api_context(db)

    barcode = f"BAR-DUP-{uuid.uuid4().hex[:8].upper()}"

    first = client.post(
        "/product-variants",
        headers=auth_headers(context["token"]),
        json={
            "product_code": context["product"].product_code,
            "sku": f"SKU-BAR-1-{uuid.uuid4().hex[:8].upper()}",
            "variant_name": "Barcode Variant One",
            "selling_price": "1000.00",
            "barcode": barcode,
        },
    )

    assert first.status_code == 201

    second = client.post(
        "/product-variants",
        headers=auth_headers(context["token"]),
        json={
            "product_code": context["product"].product_code,
            "sku": f"SKU-BAR-2-{uuid.uuid4().hex[:8].upper()}",
            "variant_name": "Barcode Variant Two",
            "selling_price": "1200.00",
            "barcode": barcode,
        },
    )

    assert second.status_code == 409
    assert second.json()["detail"] == (
        "A variant with this barcode already exists."
    )


def test_get_product_variant_api(client, db):
    context = create_product_variant_api_context(db)

    sku = f"SKU-GET-{uuid.uuid4().hex[:8].upper()}"

    create_response = client.post(
        "/product-variants",
        headers=auth_headers(context["token"]),
        json={
            "product_code": context["product"].product_code,
            "sku": sku,
            "variant_name": "Get Variant",
            "selling_price": "1499.00",
        },
    )

    assert create_response.status_code == 201

    response = client.get(
        f"/product-variants/{sku}",
        headers=auth_headers(context["token"]),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["product_id"] == str(context["product"].id)
    assert data["sku"] == sku
    assert data["variant_name"] == "Get Variant"
    assert Decimal(data["selling_price"]) == Decimal("1499.00")
    assert data["status"] == "active"


def test_get_product_variant_api_returns_404_for_unknown_sku(
    client,
    db,
):
    context = create_product_variant_api_context(db)

    response = client.get(
        "/product-variants/SKU-DOES-NOT-EXIST",
        headers=auth_headers(context["token"]),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Product variant not found."


def test_create_product_variant_api_rejects_invalid_selling_price(
    client,
    db,
):
    context = create_product_variant_api_context(db)

    response = client.post(
        "/product-variants",
        headers=auth_headers(context["token"]),
        json={
            "product_code": context["product"].product_code,
            "sku": f"SKU-INVALID-{uuid.uuid4().hex[:8].upper()}",
            "variant_name": "Invalid Price",
            "selling_price": "0",
        },
    )

    assert response.status_code == 422


def test_create_product_variant_api_rejects_invalid_tax_rate(
    client,
    db,
):
    context = create_product_variant_api_context(db)

    response = client.post(
        "/product-variants",
        headers=auth_headers(context["token"]),
        json={
            "product_code": context["product"].product_code,
            "sku": f"SKU-TAX-{uuid.uuid4().hex[:8].upper()}",
            "variant_name": "Invalid Tax",
            "selling_price": "1000.00",
            "tax_rate": "101.00",
        },
    )

    assert response.status_code == 422
