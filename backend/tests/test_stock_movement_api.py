from decimal import Decimal
from uuid import uuid4

from app.models.access_control import user_roles
from app.models.inventory_item import InventoryItem
from app.models.inventory_location import InventoryLocation
from app.models.product import Product
from app.models.product_variant import ProductVariant
from app.models.retailer import Retailer
from app.models.role import Role
from app.models.stock_movement import StockMovement
from app.models.user import User
from app.services.auth_service import create_user_token


def create_stock_movement_api_context(db):
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

    retailer = Retailer(
        retailer_id=f"RET-SM-API-{uuid4().hex[:6].upper()}",
        owner_user_id=user.id,
        business_name="Stock Movement API Retailer",
        phone_number=user.phone_number,
        status="active",
    )
    db.add(retailer)
    db.flush()

    location = InventoryLocation(
        retailer_id=retailer.id,
        name="Stock Movement API Store",
        location_type="store",
        is_active=True,
    )
    db.add(location)
    db.flush()

    product = Product(
        product_code=f"PROD-SM-API-{uuid4().hex[:6].upper()}",
        name="Stock Movement API Product",
        status="active",
    )
    db.add(product)
    db.flush()

    variant = ProductVariant(
        product_id=product.id,
        sku=f"SKU-SM-API-{uuid4().hex[:6].upper()}",
        variant_name="Stock Movement Variant",
        selling_price=Decimal("1500.00"),
        purchase_cost=Decimal("1000.00"),
        tax_rate=Decimal("18.00"),
        track_inventory=True,
        requires_serial_number=False,
        status="active",
    )
    db.add(variant)
    db.flush()

    inventory = InventoryItem(
        retailer_id=retailer.id,
        location_id=location.id,
        product_variant_id=variant.id,
        quantity_on_hand=10,
        quantity_reserved=0,
        average_cost=Decimal("1000.00"),
    )
    db.add(inventory)
    db.flush()

    db.commit()

    token = create_user_token(user)

    return {
        "user": user,
        "retailer": retailer,
        "location": location,
        "product": product,
        "variant": variant,
        "inventory": inventory,
        "token": token,
    }


def auth_headers(token):
    return {
        "Authorization": f"Bearer {token}",
    }


def test_create_stock_movement_api(client, db):
    context = create_stock_movement_api_context(db)

    response = client.post(
        "/stock-movements",
        headers=auth_headers(context["token"]),
        json={
            "location_id": str(context["location"].id),
            "sku": context["variant"].sku,
            "movement_type": "stock_in",
            "quantity": 5,
            "unit_cost": "1200.00",
            "reference_type": "manual",
            "notes": "API stock movement test",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["retailer_id"] == str(context["retailer"].id)
    assert data["location_id"] == str(context["location"].id)
    assert data["product_variant_id"] == str(
        context["variant"].id
    )
    assert data["movement_type"] == "stock_in"
    assert data["quantity"] == 5
    assert data["unit_cost"] == "1200.00"
    assert data["reference_type"] == "manual"
    assert data["notes"] == "API stock movement test"
    assert data["performed_by_user_id"] == str(
        context["user"].id
    )
    assert data["created_at"]

    db.refresh(context["inventory"])

    assert context["inventory"].quantity_on_hand == 15


def test_create_stock_out_movement_api(client, db):
    context = create_stock_movement_api_context(db)

    response = client.post(
        "/stock-movements",
        headers=auth_headers(context["token"]),
        json={
            "location_id": str(context["location"].id),
            "sku": context["variant"].sku,
            "movement_type": "stock_out",
            "quantity": 4,
            "notes": "Stock out API test",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["movement_type"] == "stock_out"
    assert data["quantity"] == 4
    assert data["unit_cost"] is None

    db.refresh(context["inventory"])

    assert context["inventory"].quantity_on_hand == 6


def test_get_stock_movements_api(client, db):
    context = create_stock_movement_api_context(db)

    for movement_type, quantity in [
        ("stock_in", 5),
        ("stock_out", 2),
    ]:
        response = client.post(
            "/stock-movements",
            headers=auth_headers(context["token"]),
            json={
                "location_id": str(context["location"].id),
                "sku": context["variant"].sku,
                "movement_type": movement_type,
                "quantity": quantity,
            },
        )

        assert response.status_code == 201

    response = client.get(
        f"/stock-movements/{context['variant'].sku}",
        params={
            "location_id": str(context["location"].id),
        },
        headers=auth_headers(context["token"]),
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 2
    assert data[0]["movement_type"] == "stock_out"
    assert data[0]["quantity"] == 2
    assert data[1]["movement_type"] == "stock_in"
    assert data[1]["quantity"] == 5


def test_stock_out_rejects_insufficient_stock(client, db):
    context = create_stock_movement_api_context(db)

    response = client.post(
        "/stock-movements",
        headers=auth_headers(context["token"]),
        json={
            "location_id": str(context["location"].id),
            "sku": context["variant"].sku,
            "movement_type": "stock_out",
            "quantity": 11,
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"] == (
        "Insufficient available stock."
    )


def test_invalid_movement_type_returns_409(client, db):
    context = create_stock_movement_api_context(db)

    response = client.post(
        "/stock-movements",
        headers=auth_headers(context["token"]),
        json={
            "location_id": str(context["location"].id),
            "sku": context["variant"].sku,
            "movement_type": "invalid_type",
            "quantity": 1,
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"] == (
        "Invalid stock movement type."
    )


def test_unknown_sku_returns_404(client, db):
    context = create_stock_movement_api_context(db)

    response = client.post(
        "/stock-movements",
        headers=auth_headers(context["token"]),
        json={
            "location_id": str(context["location"].id),
            "sku": "SKU-DOES-NOT-EXIST",
            "movement_type": "stock_in",
            "quantity": 1,
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == (
        "Product variant not found."
    )


def test_unknown_location_returns_404(client, db):
    context = create_stock_movement_api_context(db)

    response = client.post(
        "/stock-movements",
        headers=auth_headers(context["token"]),
        json={
            "location_id": str(uuid4()),
            "sku": context["variant"].sku,
            "movement_type": "stock_in",
            "quantity": 1,
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == (
        "Inventory location not found for this retailer."
    )


def test_invalid_reference_id_returns_400(client, db):
    context = create_stock_movement_api_context(db)

    response = client.post(
        "/stock-movements",
        headers=auth_headers(context["token"]),
        json={
            "location_id": str(context["location"].id),
            "sku": context["variant"].sku,
            "movement_type": "stock_in",
            "quantity": 1,
            "reference_id": "not-a-uuid",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Invalid reference ID."
    )


def test_zero_quantity_is_rejected_by_validation(client, db):
    context = create_stock_movement_api_context(db)

    response = client.post(
        "/stock-movements",
        headers=auth_headers(context["token"]),
        json={
            "location_id": str(context["location"].id),
            "sku": context["variant"].sku,
            "movement_type": "stock_in",
            "quantity": 0,
        },
    )

    assert response.status_code == 422


def test_negative_quantity_is_rejected_by_validation(client, db):
    context = create_stock_movement_api_context(db)

    response = client.post(
        "/stock-movements",
        headers=auth_headers(context["token"]),
        json={
            "location_id": str(context["location"].id),
            "sku": context["variant"].sku,
            "movement_type": "stock_in",
            "quantity": -1,
        },
    )

    assert response.status_code == 422


def test_get_stock_movements_unknown_sku_returns_404(
    client,
    db,
):
    context = create_stock_movement_api_context(db)

    response = client.get(
        "/stock-movements/SKU-DOES-NOT-EXIST",
        params={
            "location_id": str(context["location"].id),
        },
        headers=auth_headers(context["token"]),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == (
        "Product variant not found."
    )


def test_create_stock_movement_rejects_inactive_retailer(
    client,
    db,
):
    context = create_stock_movement_api_context(db)

    context["retailer"].status = "pending"
    db.commit()

    response = client.post(
        "/stock-movements",
        headers=auth_headers(context["token"]),
        json={
            "location_id": str(context["location"].id),
            "sku": context["variant"].sku,
            "movement_type": "stock_in",
            "quantity": 1,
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "Retailer is not active."


def test_create_stock_movement_missing_inventory_item(
    client,
    db,
):
    context = create_stock_movement_api_context(db)

    db.delete(context["inventory"])
    db.commit()

    response = client.post(
        "/stock-movements",
        headers=auth_headers(context["token"]),
        json={
            "location_id": str(context["location"].id),
            "sku": context["variant"].sku,
            "movement_type": "stock_in",
            "quantity": 1,
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Inventory item not found."


def test_stock_movement_with_reference_id(
    client,
    db,
):
    context = create_stock_movement_api_context(db)

    reference_id = str(uuid4())

    response = client.post(
        "/stock-movements",
        headers=auth_headers(context["token"]),
        json={
            "location_id": str(context["location"].id),
            "sku": context["variant"].sku,
            "movement_type": "stock_in",
            "quantity": 3,
            "reference_type": "purchase_order",
            "reference_id": reference_id,
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["reference_type"] == "purchase_order"
    assert data["reference_id"] == reference_id


def test_negative_unit_cost_is_rejected(
    client,
    db,
):
    context = create_stock_movement_api_context(db)

    response = client.post(
        "/stock-movements",
        headers=auth_headers(context["token"]),
        json={
            "location_id": str(context["location"].id),
            "sku": context["variant"].sku,
            "movement_type": "stock_in",
            "quantity": 1,
            "unit_cost": "-10.00",
        },
    )

    assert response.status_code == 422


def test_stock_out_respects_reserved_quantity(
    client,
    db,
):
    context = create_stock_movement_api_context(db)

    context["inventory"].quantity_reserved = 8
    db.commit()

    response = client.post(
        "/stock-movements",
        headers=auth_headers(context["token"]),
        json={
            "location_id": str(context["location"].id),
            "sku": context["variant"].sku,
            "movement_type": "stock_out",
            "quantity": 3,
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"] == (
        "Insufficient available stock."
    )


def test_stock_in_updates_average_cost(
    client,
    db,
):
    context = create_stock_movement_api_context(db)

    response = client.post(
        "/stock-movements",
        headers=auth_headers(context["token"]),
        json={
            "location_id": str(context["location"].id),
            "sku": context["variant"].sku,
            "movement_type": "purchase",
            "quantity": 10,
            "unit_cost": "1200.00",
        },
    )

    assert response.status_code == 201

    db.refresh(context["inventory"])

    # Existing: 10 units @ 1000
    # New:      10 units @ 1200
    # Average:  1100
    assert context["inventory"].quantity_on_hand == 20
    assert context["inventory"].average_cost == Decimal(
        "1100.00"
    )


def test_get_stock_movements_requires_location(
    client,
    db,
):
    context = create_stock_movement_api_context(db)

    response = client.get(
        f"/stock-movements/{context['variant'].sku}",
        headers=auth_headers(context["token"]),
    )

    assert response.status_code == 422


def test_get_stock_movements_unknown_location_returns_404(
    client,
    db,
):
    context = create_stock_movement_api_context(db)

    response = client.get(
        f"/stock-movements/{context['variant'].sku}",
        params={
            "location_id": str(uuid4()),
        },
        headers=auth_headers(context["token"]),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == (
        "Inventory location not found for this retailer."
    )
