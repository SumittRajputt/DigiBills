from decimal import Decimal
from uuid import uuid4

from app.models.inventory_item import InventoryItem
from app.models.inventory_location import InventoryLocation
from app.models.product import Product
from app.models.product_variant import ProductVariant
from app.models.retailer import Retailer
from app.models.role import Role
from app.models.supplier import Supplier
from app.models.user import User
from app.models.access_control import user_roles
from app.services.auth_service import create_user_token


def create_purchase_order_api_context(db):
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
        retailer_id=f"RET-PO-API-{uuid4().hex[:6].upper()}",
        owner_user_id=user.id,
        business_name="Purchase Order API Retailer",
        phone_number=user.phone_number,
        status="active",
    )
    db.add(retailer)
    db.flush()

    supplier = Supplier(
        supplier_id=f"SUP-PO-API-{uuid4().hex[:6].upper()}",
        retailer_id=retailer.id,
        name="Purchase Order API Supplier",
        phone_number=f"8{uuid4().hex[:9]}",
        is_active=True,
    )
    db.add(supplier)
    db.flush()

    location = InventoryLocation(
        retailer_id=retailer.id,
        name="Purchase Order API Store",
        location_type="store",
        is_active=True,
    )
    db.add(location)
    db.flush()

    product = Product(
        product_code=f"PROD-PO-API-{uuid4().hex[:6].upper()}",
        name="Purchase Order API Product",
        status="active",
    )
    db.add(product)
    db.flush()

    variant = ProductVariant(
        product_id=product.id,
        sku=f"SKU-PO-API-{uuid4().hex[:6].upper()}",
        variant_name="Purchase Order API Variant",
        purchase_cost=Decimal("1000.00"),
        selling_price=Decimal("1500.00"),
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
        quantity_on_hand=0,
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
        "supplier": supplier,
        "location": location,
        "variant": variant,
        "inventory": inventory,
        "token": token,
    }


def auth_headers(token):
    return {
        "Authorization": f"Bearer {token}",
    }


def create_purchase_order(client, context):
    response = client.post(
        "/purchase-orders",
        headers=auth_headers(context["token"]),
        json={
            "supplier_id": context["supplier"].supplier_id,
            "location_id": str(context["location"].id),
            "notes": "API purchase order test",
        },
    )

    assert response.status_code == 201

    return response


def test_create_purchase_order_api(client, db):
    context = create_purchase_order_api_context(db)

    response = create_purchase_order(client, context)

    data = response.json()

    assert data["status"] == "draft"
    assert data["supplier_id"] == str(context["supplier"].id)
    assert data["location_id"] == str(context["location"].id)
    assert data["retailer_id"] == str(context["retailer"].id)
    assert data["created_by_user_id"] == str(context["user"].id)
    assert data["subtotal"] == "0.00"
    assert data["tax_amount"] == "0.00"
    assert data["total_amount"] == "0.00"


def test_create_purchase_order_api_rejects_unknown_supplier(
    client,
    db,
):
    context = create_purchase_order_api_context(db)

    response = client.post(
        "/purchase-orders",
        headers=auth_headers(context["token"]),
        json={
            "supplier_id": "SUP-DOES-NOT-EXIST",
            "location_id": str(context["location"].id),
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Supplier not found."


def test_add_purchase_order_item_api(client, db):
    context = create_purchase_order_api_context(db)

    response = create_purchase_order(client, context)

    purchase_order_id = response.json()["purchase_order_id"]

    response = client.post(
        f"/purchase-orders/{purchase_order_id}/items",
        headers=auth_headers(context["token"]),
        json={
            "sku": context["variant"].sku,
            "ordered_quantity": 10,
            "unit_cost": "1000.00",
            "tax_rate": "18.00",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["purchase_order_id"] == purchase_order_id
    assert data["sku"] == context["variant"].sku
    assert data["ordered_quantity"] == 10
    assert data["received_quantity"] == 0
    assert data["unit_cost"] == "1000.00"
    assert data["tax_rate"] == "18.00"
    assert data["tax_amount"] == "1800.00"
    assert data["line_total"] == "11800.00"


def test_list_purchase_orders_api(client, db):
    context = create_purchase_order_api_context(db)

    first = create_purchase_order(client, context)
    second = create_purchase_order(client, context)

    assert first.status_code == 201
    assert second.status_code == 201

    response = client.get(
        "/purchase-orders",
        headers=auth_headers(context["token"]),
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 2
    assert all(
        order["retailer_id"] == str(context["retailer"].id)
        for order in data
    )


def test_get_purchase_order_api(client, db):
    context = create_purchase_order_api_context(db)

    response = create_purchase_order(client, context)

    purchase_order_id = response.json()["purchase_order_id"]

    response = client.get(
        f"/purchase-orders/{purchase_order_id}",
        headers=auth_headers(context["token"]),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["purchase_order_id"] == purchase_order_id
    assert data["status"] == "draft"


def test_get_purchase_order_items_api(client, db):
    context = create_purchase_order_api_context(db)

    response = create_purchase_order(client, context)

    purchase_order_id = response.json()["purchase_order_id"]

    item_response = client.post(
        f"/purchase-orders/{purchase_order_id}/items",
        headers=auth_headers(context["token"]),
        json={
            "sku": context["variant"].sku,
            "ordered_quantity": 5,
            "unit_cost": "1000.00",
            "tax_rate": "18.00",
        },
    )

    assert item_response.status_code == 201

    response = client.get(
        f"/purchase-orders/{purchase_order_id}/items",
        headers=auth_headers(context["token"]),
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["sku"] == context["variant"].sku
    assert data[0]["ordered_quantity"] == 5
    assert data[0]["received_quantity"] == 0


def test_update_purchase_order_status_api(client, db):
    context = create_purchase_order_api_context(db)

    response = create_purchase_order(client, context)

    purchase_order_id = response.json()["purchase_order_id"]

    response = client.patch(
        f"/purchase-orders/{purchase_order_id}/status",
        params={
            "new_status": "ordered",
        },
        headers=auth_headers(context["token"]),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["purchase_order_id"] == purchase_order_id
    assert data["status"] == "ordered"


def test_receive_purchase_order_item_api_updates_inventory(
    client,
    db,
):
    context = create_purchase_order_api_context(db)

    response = create_purchase_order(client, context)

    purchase_order_id = response.json()["purchase_order_id"]

    item_response = client.post(
        f"/purchase-orders/{purchase_order_id}/items",
        headers=auth_headers(context["token"]),
        json={
            "sku": context["variant"].sku,
            "ordered_quantity": 10,
            "unit_cost": "1000.00",
            "tax_rate": "18.00",
        },
    )

    assert item_response.status_code == 201

    item_id = item_response.json()["id"]

    status_response = client.patch(
        f"/purchase-orders/{purchase_order_id}/status",
        params={
            "new_status": "ordered",
        },
        headers=auth_headers(context["token"]),
    )

    assert status_response.status_code == 200

    response = client.post(
        f"/purchase-orders/{purchase_order_id}/items/{item_id}/receive",
        headers=auth_headers(context["token"]),
        json={
            "received_quantity": 4,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == item_id
    assert data["ordered_quantity"] == 10
    assert data["received_quantity"] == 4

    db.refresh(context["inventory"])

    assert context["inventory"].quantity_on_hand == 4


def test_receive_purchase_order_item_api_rejects_invalid_item(
    client,
    db,
):
    context = create_purchase_order_api_context(db)

    response = create_purchase_order(client, context)

    purchase_order_id = response.json()["purchase_order_id"]

    status_response = client.patch(
        f"/purchase-orders/{purchase_order_id}/status",
        params={
            "new_status": "ordered",
        },
        headers=auth_headers(context["token"]),
    )

    assert status_response.status_code == 200

    response = client.post(
        f"/purchase-orders/{purchase_order_id}/items/not-a-uuid/receive",
        headers=auth_headers(context["token"]),
        json={
            "received_quantity": 1,
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Invalid purchase order item ID."
    )


def test_get_purchase_order_api_rejects_unknown_order(
    client,
    db,
):
    context = create_purchase_order_api_context(db)

    response = client.get(
        "/purchase-orders/PO-DOES-NOT-EXIST",
        headers=auth_headers(context["token"]),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == (
        "Purchase order not found."
    )
