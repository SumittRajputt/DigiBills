from decimal import Decimal
from uuid import uuid4

from app.models.inventory_item import InventoryItem
from app.models.inventory_location import InventoryLocation
from app.models.product import Product
from app.models.product_variant import ProductVariant
from app.models.retailer import Retailer
from app.models.role import Role
from app.models.user import User
from app.models.access_control import user_roles
from app.services.auth_service import create_user_token


def create_inventory_api_context(db):
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
        retailer_id=f"RET-INV-API-{uuid4().hex[:6].upper()}",
        owner_user_id=user.id,
        business_name="Inventory API Retailer",
        phone_number=user.phone_number,
        status="active",
    )
    db.add(retailer)
    db.flush()

    location = InventoryLocation(
        retailer_id=retailer.id,
        name="Inventory API Store",
        location_type="store",
        is_active=True,
    )
    db.add(location)
    db.flush()

    product = Product(
        product_code=f"PROD-INV-API-{uuid4().hex[:6].upper()}",
        name="Inventory API Product",
        status="active",
    )
    db.add(product)
    db.flush()

    variant = ProductVariant(
        product_id=product.id,
        sku=f"SKU-INV-API-{uuid4().hex[:6].upper()}",
        variant_name="Inventory API Variant",
        purchase_cost=Decimal("1000.00"),
        selling_price=Decimal("1500.00"),
        tax_rate=Decimal("18.00"),
        track_inventory=True,
        requires_serial_number=False,
        status="active",
    )
    db.add(variant)
    db.flush()

    db.commit()

    token = create_user_token(user)

    return {
        "user": user,
        "retailer": retailer,
        "location": location,
        "product": product,
        "variant": variant,
        "token": token,
    }


def auth_headers(token):
    return {
        "Authorization": f"Bearer {token}",
    }


def test_create_inventory_api(client, db):
    context = create_inventory_api_context(db)

    response = client.post(
        "/inventory",
        headers=auth_headers(context["token"]),
        json={
            "location_id": str(context["location"].id),
            "sku": context["variant"].sku,
            "reorder_level": 5,
            "reorder_quantity": 10,
            "average_cost": "1000.00",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["retailer_id"] == str(context["retailer"].id)
    assert data["location_id"] == str(context["location"].id)
    assert data["product_variant_id"] == str(context["variant"].id)
    assert data["quantity_on_hand"] == 0
    assert data["quantity_reserved"] == 0
    assert data["quantity_available"] == 0
    assert data["reorder_level"] == 5
    assert data["reorder_quantity"] == 10
    assert data["average_cost"] == "1000.00"


def test_create_inventory_api_rejects_duplicate(
    client,
    db,
):
    context = create_inventory_api_context(db)

    payload = {
        "location_id": str(context["location"].id),
        "sku": context["variant"].sku,
        "reorder_level": 5,
        "reorder_quantity": 10,
        "average_cost": "1000.00",
    }

    first = client.post(
        "/inventory",
        headers=auth_headers(context["token"]),
        json=payload,
    )

    assert first.status_code == 201

    second = client.post(
        "/inventory",
        headers=auth_headers(context["token"]),
        json=payload,
    )

    assert second.status_code == 409


def test_create_inventory_api_rejects_unknown_sku(
    client,
    db,
):
    context = create_inventory_api_context(db)

    response = client.post(
        "/inventory",
        headers=auth_headers(context["token"]),
        json={
            "location_id": str(context["location"].id),
            "sku": "SKU-DOES-NOT-EXIST",
            "average_cost": "1000.00",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Product variant not found."


def test_create_inventory_api_rejects_unknown_location(
    client,
    db,
):
    context = create_inventory_api_context(db)

    response = client.post(
        "/inventory",
        headers=auth_headers(context["token"]),
        json={
            "location_id": str(uuid4()),
            "sku": context["variant"].sku,
            "average_cost": "1000.00",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == (
        "Inventory location not found for this retailer."
    )


def test_get_inventory_api(
    client,
    db,
):
    context = create_inventory_api_context(db)

    inventory = InventoryItem(
        retailer_id=context["retailer"].id,
        location_id=context["location"].id,
        product_variant_id=context["variant"].id,
        quantity_on_hand=20,
        quantity_reserved=5,
        average_cost=Decimal("1000.00"),
        reorder_level=5,
        reorder_quantity=10,
    )
    db.add(inventory)
    db.commit()

    response = client.get(
        f"/inventory/{context['variant'].sku}",
        params={
            "location_id": str(context["location"].id),
        },
        headers=auth_headers(context["token"]),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["quantity_on_hand"] == 20
    assert data["quantity_reserved"] == 5
    assert data["quantity_available"] == 15
    assert data["reorder_level"] == 5
    assert data["reorder_quantity"] == 10
    assert data["average_cost"] == "1000.00"


def test_get_inventory_api_rejects_unknown_sku(
    client,
    db,
):
    context = create_inventory_api_context(db)

    response = client.get(
        "/inventory/SKU-DOES-NOT-EXIST",
        params={
            "location_id": str(context["location"].id),
        },
        headers=auth_headers(context["token"]),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Product variant not found."


def test_get_inventory_api_rejects_missing_inventory(
    client,
    db,
):
    context = create_inventory_api_context(db)

    response = client.get(
        f"/inventory/{context['variant'].sku}",
        params={
            "location_id": str(context["location"].id),
        },
        headers=auth_headers(context["token"]),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Inventory item not found."


def test_reorder_status_api_returns_reorder_required(
    client,
    db,
):
    context = create_inventory_api_context(db)

    inventory = InventoryItem(
        retailer_id=context["retailer"].id,
        location_id=context["location"].id,
        product_variant_id=context["variant"].id,
        quantity_on_hand=3,
        quantity_reserved=0,
        average_cost=Decimal("1000.00"),
        reorder_level=5,
        reorder_quantity=10,
    )
    db.add(inventory)
    db.commit()

    response = client.get(
        f"/inventory/{context['variant'].sku}/reorder-status",
        params={
            "location_id": str(context["location"].id),
        },
        headers=auth_headers(context["token"]),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["needs_reorder"] is True


def test_reorder_status_api_returns_no_reorder_when_stock_is_above_level(
    client,
    db,
):
    context = create_inventory_api_context(db)

    inventory = InventoryItem(
        retailer_id=context["retailer"].id,
        location_id=context["location"].id,
        product_variant_id=context["variant"].id,
        quantity_on_hand=20,
        quantity_reserved=0,
        average_cost=Decimal("1000.00"),
        reorder_level=5,
        reorder_quantity=10,
    )
    db.add(inventory)
    db.commit()

    response = client.get(
        f"/inventory/{context['variant'].sku}/reorder-status",
        params={
            "location_id": str(context["location"].id),
        },
        headers=auth_headers(context["token"]),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["needs_reorder"] is False


def test_reorder_status_api_rejects_missing_inventory(
    client,
    db,
):
    context = create_inventory_api_context(db)

    response = client.get(
        f"/inventory/{context['variant'].sku}/reorder-status",
        params={
            "location_id": str(context["location"].id),
        },
        headers=auth_headers(context["token"]),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Inventory item not found."
