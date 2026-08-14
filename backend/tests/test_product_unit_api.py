from uuid import uuid4

from app.models.product import Product
from app.models.product_variant import ProductVariant
from app.models.role import Role
from app.models.user import User
from app.models.access_control import user_roles
from app.services.auth_service import create_user_token


def test_create_product_unit_api(client, db):
    user = User(
        phone_number=f"999{uuid4().hex[:7]}",
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
        product_code=f"PROD-API-{uuid4().hex[:8].upper()}",
        name="API Serialized Product",
        status="active",
    )
    db.add(product)
    db.flush()

    variant = ProductVariant(
        product_id=product.id,
        sku=f"SKU-API-{uuid4().hex[:8].upper()}",
        variant_name="Serialized Variant",
        selling_price=15000,
        purchase_cost=10000,
        tax_rate=18,
        track_inventory=True,
        requires_serial_number=True,
        status="active",
    )
    db.add(variant)
    db.commit()

    token = create_user_token(user)

    serial_number = f"SN-API-{uuid4().hex[:12].upper()}"

    response = client.post(
        "/product-units",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "product_variant_id": str(variant.id),
            "serial_number": serial_number,
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["product_variant_id"] == str(variant.id)
    assert data["serial_number"] == serial_number
    assert data["status"] == "in_stock"


def test_create_product_unit_api_rejects_non_serialized_variant(
    client,
    db,
):
    user = User(
        phone_number=f"999{uuid4().hex[:7]}",
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
        product_code=f"PROD-API-{uuid4().hex[:8].upper()}",
        name="API Non Serialized Product",
        status="active",
    )
    db.add(product)
    db.flush()

    variant = ProductVariant(
        product_id=product.id,
        sku=f"SKU-API-{uuid4().hex[:8].upper()}",
        variant_name="Non Serialized Variant",
        selling_price=150,
        purchase_cost=100,
        tax_rate=18,
        track_inventory=True,
        requires_serial_number=False,
        status="active",
    )
    db.add(variant)
    db.commit()

    token = create_user_token(user)

    response = client.post(
        "/product-units",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "product_variant_id": str(variant.id),
            "serial_number": f"SN-API-{uuid4().hex[:12].upper()}",
        },
    )

    assert response.status_code == 409
    assert "does not require serial number tracking" in response.json()["detail"]
