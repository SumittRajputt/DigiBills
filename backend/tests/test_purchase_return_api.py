from decimal import Decimal
from uuid import uuid4

from app.models.inventory_item import InventoryItem
from app.models.inventory_location import InventoryLocation
from app.models.product import Product
from app.models.product_variant import ProductVariant
from app.models.purchase_order import PurchaseOrder
from app.models.purchase_order_item import PurchaseOrderItem
from app.models.retailer import Retailer
from app.models.role import Role
from app.models.supplier import Supplier
from app.models.user import User
from app.models.access_control import user_roles
from app.services.auth_service import create_user_token
from app.services.purchase_order_service import (
    add_purchase_order_item,
    create_purchase_order,
    update_purchase_order_status,
)
from app.services.stock_movement_service import create_stock_movement


def create_purchase_return_api_context(db):
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
        retailer_id=f"RET-PR-API-{uuid4().hex[:6].upper()}",
        owner_user_id=user.id,
        business_name="Purchase Return API Retailer",
        phone_number=user.phone_number,
        status="active",
    )
    db.add(retailer)
    db.flush()

    supplier = Supplier(
        supplier_id=f"SUP-PR-API-{uuid4().hex[:6].upper()}",
        retailer_id=retailer.id,
        name="Purchase Return API Supplier",
        phone_number=f"8{uuid4().hex[:9]}",
        is_active=True,
    )
    db.add(supplier)
    db.flush()

    location = InventoryLocation(
        retailer_id=retailer.id,
        name="Purchase Return API Store",
        location_type="store",
        is_active=True,
    )
    db.add(location)
    db.flush()

    product = Product(
        product_code=f"PROD-PR-API-{uuid4().hex[:6].upper()}",
        name="Purchase Return API Product",
        status="active",
    )
    db.add(product)
    db.flush()

    variant = ProductVariant(
        product_id=product.id,
        sku=f"SKU-PR-API-{uuid4().hex[:6].upper()}",
        variant_name="Purchase Return API Variant",
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

    purchase_order = create_purchase_order(
        db=db,
        retailer=retailer,
        supplier=supplier,
        location=location,
        created_by_user=user,
    )

    purchase_order_item = add_purchase_order_item(
        db=db,
        purchase_order=purchase_order,
        product_variant=variant,
        ordered_quantity=10,
        unit_cost=Decimal("1000.00"),
        tax_rate=Decimal("18.00"),
    )

    update_purchase_order_status(
        db=db,
        purchase_order=purchase_order,
        status="ordered",
    )

    create_stock_movement(
        db=db,
        retailer=retailer,
        location=location,
        product_variant=variant,
        inventory_item=inventory,
        movement_type="purchase",
        quantity=10,
        unit_cost=Decimal("1000.00"),
        reference_type="purchase_order",
        reference_id=purchase_order.id,
        notes="Purchase return API test stock",
        commit=True,
    )

    purchase_order_item.received_quantity = 10
    purchase_order.status = "received"
    db.commit()
    db.refresh(purchase_order)
    db.refresh(purchase_order_item)
    db.refresh(inventory)

    token = create_user_token(user)

    return {
        "user": user,
        "retailer": retailer,
        "supplier": supplier,
        "location": location,
        "product": product,
        "variant": variant,
        "inventory": inventory,
        "purchase_order": purchase_order,
        "purchase_order_item": purchase_order_item,
        "token": token,
    }


def auth_headers(token):
    return {
        "Authorization": f"Bearer {token}",
    }


def create_purchase_return(client, context):
    response = client.post(
        "/purchase-returns",
        headers=auth_headers(context["token"]),
        json={
            "purchase_order_id": (
                context["purchase_order"].purchase_order_id
            ),
            "reason": "Damaged goods",
            "notes": "API purchase return test",
        },
    )

    assert response.status_code == 201

    return response


def test_create_purchase_return_api(client, db):
    context = create_purchase_return_api_context(db)

    response = create_purchase_return(client, context)

    data = response.json()

    assert data["status"] == "requested"
    assert data["purchase_order_id"] == str(
        context["purchase_order"].id
    )
    assert data["retailer_id"] == str(
        context["retailer"].id
    )
    assert data["supplier_id"] == str(
        context["supplier"].id
    )
    assert data["location_id"] == str(
        context["location"].id
    )
    assert data["return_amount"] == "0.00"
    assert data["reason"] == "Damaged goods"
    assert data["notes"] == "API purchase return test"


def test_create_purchase_return_api_rejects_unknown_purchase_order(
    client,
    db,
):
    context = create_purchase_return_api_context(db)

    response = client.post(
        "/purchase-returns",
        headers=auth_headers(context["token"]),
        json={
            "purchase_order_id": "PO-DOES-NOT-EXIST",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Purchase order not found."


def test_list_purchase_returns_api(client, db):
    context = create_purchase_return_api_context(db)

    first = create_purchase_return(client, context)

    context2 = create_purchase_return_api_context(db)

    second = create_purchase_return(client, context2)

    assert first.status_code == 201
    assert second.status_code == 201

    response = client.get(
        "/purchase-returns",
        headers=auth_headers(context["token"]),
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["return_id"] == first.json()["return_id"]


def test_get_purchase_return_api(client, db):
    context = create_purchase_return_api_context(db)

    response = create_purchase_return(client, context)

    return_id = response.json()["return_id"]

    response = client.get(
        f"/purchase-returns/{return_id}",
        headers=auth_headers(context["token"]),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["return_id"] == return_id
    assert data["status"] == "requested"


def test_get_purchase_return_api_returns_404_for_unknown_return(
    client,
    db,
):
    context = create_purchase_return_api_context(db)

    response = client.get(
        "/purchase-returns/PR-DOES-NOT-EXIST",
        headers=auth_headers(context["token"]),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Purchase return not found."


def test_add_purchase_return_item_api(client, db):
    context = create_purchase_return_api_context(db)

    response = create_purchase_return(client, context)

    return_id = response.json()["return_id"]

    response = client.post(
        f"/purchase-returns/{return_id}/items",
        headers=auth_headers(context["token"]),
        json={
            "purchase_order_item_id": str(
                context["purchase_order_item"].id
            ),
            "quantity": 3,
            "reason": "Damaged",
            "condition": "damaged",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["purchase_return_id"] == str(
        response.json()["purchase_return_id"]
    )
    assert data["purchase_order_item_id"] == str(
        context["purchase_order_item"].id
    )
    assert data["product_variant_id"] == str(
        context["variant"].id
    )
    assert data["sku"] == context["variant"].sku
    assert data["quantity"] == 3
    assert data["unit_cost"] == "1000.00"
    assert data["return_amount"] == "3000.00"
    assert data["reason"] == "Damaged"
    assert data["condition"] == "damaged"


def test_add_purchase_return_item_api_rejects_invalid_item_id(
    client,
    db,
):
    context = create_purchase_return_api_context(db)

    response = create_purchase_return(client, context)

    return_id = response.json()["return_id"]

    response = client.post(
        f"/purchase-returns/{return_id}/items",
        headers=auth_headers(context["token"]),
        json={
            "purchase_order_item_id": "not-a-uuid",
            "quantity": 1,
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Invalid purchase order item ID."
    )


def test_get_purchase_return_items_api(client, db):
    context = create_purchase_return_api_context(db)

    response = create_purchase_return(client, context)

    return_id = response.json()["return_id"]

    item_response = client.post(
        f"/purchase-returns/{return_id}/items",
        headers=auth_headers(context["token"]),
        json={
            "purchase_order_item_id": str(
                context["purchase_order_item"].id
            ),
            "quantity": 2,
            "condition": "good",
        },
    )

    assert item_response.status_code == 201

    response = client.get(
        f"/purchase-returns/{return_id}/items",
        headers=auth_headers(context["token"]),
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["quantity"] == 2
    assert data[0]["return_amount"] == "2000.00"


def test_process_purchase_return_api(client, db):
    context = create_purchase_return_api_context(db)

    response = create_purchase_return(client, context)

    return_id = response.json()["return_id"]

    item_response = client.post(
        f"/purchase-returns/{return_id}/items",
        headers=auth_headers(context["token"]),
        json={
            "purchase_order_item_id": str(
                context["purchase_order_item"].id
            ),
            "quantity": 4,
            "condition": "damaged",
        },
    )

    assert item_response.status_code == 201

    response = client.post(
        f"/purchase-returns/{return_id}/process",
        headers=auth_headers(context["token"]),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["return_id"] == return_id
    assert data["status"] == "processed"
    assert data["processed_by_user_id"] == str(
        context["user"].id
    )
    assert data["processed_at"] is not None

    db.refresh(context["inventory"])

    assert context["inventory"].quantity_on_hand == 6


def test_process_purchase_return_api_rejects_empty_return(
    client,
    db,
):
    context = create_purchase_return_api_context(db)

    response = create_purchase_return(client, context)

    return_id = response.json()["return_id"]

    response = client.post(
        f"/purchase-returns/{return_id}/process",
        headers=auth_headers(context["token"]),
    )

    assert response.status_code == 409
    assert response.json()["detail"] == (
        "Purchase return must contain at least one item."
    )
