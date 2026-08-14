from decimal import Decimal
from uuid import uuid4

from app.models.access_control import user_roles
from app.models.customer import Customer
from app.models.inventory_item import InventoryItem
from app.models.inventory_location import InventoryLocation
from app.models.product import Product
from app.models.product_variant import ProductVariant
from app.models.retailer import Retailer
from app.models.role import Role
from app.models.user import User
from app.services.auth_service import create_user_token
from app.schemas.invoice import InvoiceItemCreateRequest
from app.services.invoice_service import create_invoice
from app.services.stock_movement_service import create_stock_movement


def create_sales_return_api_context(db):
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
        retailer_id=f"RET-SR-API-{uuid4().hex[:6].upper()}",
        owner_user_id=user.id,
        business_name="Sales Return API Retailer",
        phone_number=user.phone_number,
        status="active",
    )
    db.add(retailer)
    db.flush()

    location = InventoryLocation(
        retailer_id=retailer.id,
        name="Sales Return API Store",
        location_type="store",
        is_active=True,
    )
    db.add(location)
    db.flush()

    customer_user = User(
        phone_number=f"8{uuid4().hex[:9]}",
        status="active",
    )
    db.add(customer_user)
    db.flush()

    customer = Customer(
        customer_id=f"CUS-SR-API-{uuid4().hex[:6].upper()}",
        user_id=customer_user.id,
        full_name="Sales Return API Customer",
        phone_number=customer_user.phone_number,
        status="active",
    )
    db.add(customer)
    db.flush()

    product = Product(
        product_code=f"PROD-SR-API-{uuid4().hex[:6].upper()}",
        name="Sales Return API Product",
        status="active",
    )
    db.add(product)
    db.flush()

    variant = ProductVariant(
        product_id=product.id,
        sku=f"SKU-SR-API-{uuid4().hex[:6].upper()}",
        variant_name="Sales Return API Variant",
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

    invoice = create_invoice(
        db=db,
        retailer=retailer,
        customer=customer,
        location=location,
        items=[
            InvoiceItemCreateRequest(
                sku=variant.sku,
                quantity=4,
            )
        ],
    )

    db.refresh(invoice)

    invoice_item = invoice.items[0]

    return {
        "user": user,
        "retailer": retailer,
        "location": location,
        "customer": customer,
        "product": product,
        "variant": variant,
        "inventory": inventory,
        "invoice": invoice,
        "invoice_item": invoice_item,
        "token": token,
    }


def auth_headers(token):
    return {
        "Authorization": f"Bearer {token}",
    }


def create_sales_return(client, context):
    response = client.post(
        "/sales-returns",
        headers=auth_headers(context["token"]),
        json={
            "invoice_id": context["invoice"].invoice_id,
            "reason": "Customer return",
            "notes": "API sales return test",
        },
    )

    assert response.status_code == 201

    return response


def test_create_sales_return_api(client, db):
    context = create_sales_return_api_context(db)

    response = create_sales_return(client, context)

    data = response.json()

    assert data["status"] == "requested"
    assert data["invoice_id"] == str(
        context["invoice"].id
    )
    assert data["retailer_id"] == str(
        context["retailer"].id
    )
    assert data["customer_id"] == str(
        context["customer"].id
    )
    assert data["return_amount"] == "0.00"
    assert data["refund_amount"] == "0.00"
    assert data["refund_method"] is None
    assert data["reason"] == "Customer return"
    assert data["notes"] == "API sales return test"
    assert data["items"] == []


def test_create_sales_return_api_rejects_unknown_invoice(
    client,
    db,
):
    context = create_sales_return_api_context(db)

    response = client.post(
        "/sales-returns",
        headers=auth_headers(context["token"]),
        json={
            "invoice_id": "INV-DOES-NOT-EXIST",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Invoice not found."


def test_add_sales_return_item_api(client, db):
    context = create_sales_return_api_context(db)

    response = create_sales_return(client, context)

    return_id = response.json()["return_id"]

    response = client.post(
        f"/sales-returns/{return_id}/items",
        headers=auth_headers(context["token"]),
        json={
            "invoice_item_id": str(
                context["invoice_item"].id
            ),
            "quantity": 2,
            "condition": "good",
            "return_to_inventory": True,
            "restocking_fee": "100.00",
            "reason": "Customer changed mind",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["return_id"] == return_id
    assert data["status"] == "requested"
    assert data["return_amount"] == "3000.00"
    assert data["refund_amount"] == "2900.00"

    assert len(data["items"]) == 1

    item = data["items"][0]

    assert item["invoice_item_id"] == str(
        context["invoice_item"].id
    )
    assert item["product_variant_id"] == str(
        context["variant"].id
    )
    assert item["sku"] == context["variant"].sku
    assert item["quantity"] == 2
    assert item["unit_price"] == "1500.00"
    assert item["return_amount"] == "3000.00"
    assert item["restocking_fee"] == "100.00"
    assert item["refund_amount"] == "2900.00"
    assert item["condition"] == "good"
    assert item["return_to_inventory"] is True
    assert item["reason"] == "Customer changed mind"


def test_add_sales_return_item_api_rejects_unknown_invoice_item(
    client,
    db,
):
    context = create_sales_return_api_context(db)

    response = create_sales_return(client, context)

    return_id = response.json()["return_id"]

    response = client.post(
        f"/sales-returns/{return_id}/items",
        headers=auth_headers(context["token"]),
        json={
            "invoice_item_id": str(uuid4()),
            "quantity": 1,
            "condition": "good",
            "return_to_inventory": True,
            "restocking_fee": "0.00",
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "Invoice item not found."


def test_add_sales_return_item_api_rejects_excess_quantity(
    client,
    db,
):
    context = create_sales_return_api_context(db)

    response = create_sales_return(client, context)

    return_id = response.json()["return_id"]

    response = client.post(
        f"/sales-returns/{return_id}/items",
        headers=auth_headers(context["token"]),
        json={
            "invoice_item_id": str(
                context["invoice_item"].id
            ),
            "quantity": 5,
            "condition": "good",
            "return_to_inventory": True,
            "restocking_fee": "0.00",
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"] == (
        "Return quantity cannot exceed sold quantity."
    )


def test_process_sales_return_api_returns_stock_to_inventory(
    client,
    db,
):
    context = create_sales_return_api_context(db)

    response = create_sales_return(client, context)

    return_id = response.json()["return_id"]

    item_response = client.post(
        f"/sales-returns/{return_id}/items",
        headers=auth_headers(context["token"]),
        json={
            "invoice_item_id": str(
                context["invoice_item"].id
            ),
            "quantity": 2,
            "condition": "good",
            "return_to_inventory": True,
            "restocking_fee": "0.00",
        },
    )

    assert item_response.status_code == 200

    response = client.post(
        f"/sales-returns/{return_id}/process",
        headers=auth_headers(context["token"]),
        json={
            "refund_method": "cash",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["return_id"] == return_id
    assert data["status"] == "processed"
    assert data["refund_method"] == "cash"
    assert data["processed_by_user_id"] == str(
        context["user"].id
    )
    assert data["processed_at"] is not None
    assert data["refund_amount"] == "3000.00"

    db.refresh(context["inventory"])

    # Invoice creation reduced inventory 10 -> 6.
    # Sales return puts 2 back: 6 -> 8.
    assert context["inventory"].quantity_on_hand == 8


def test_process_sales_return_api_reduces_stock_when_not_returned(
    client,
    db,
):
    context = create_sales_return_api_context(db)

    response = create_sales_return(client, context)

    return_id = response.json()["return_id"]

    item_response = client.post(
        f"/sales-returns/{return_id}/items",
        headers=auth_headers(context["token"]),
        json={
            "invoice_item_id": str(
                context["invoice_item"].id
            ),
            "quantity": 2,
            "condition": "defective",
            "return_to_inventory": False,
            "restocking_fee": "0.00",
        },
    )

    assert item_response.status_code == 200

    response = client.post(
        f"/sales-returns/{return_id}/process",
        headers=auth_headers(context["token"]),
        json={
            "refund_method": "cash",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "processed"
    assert data["refund_method"] == "cash"

    db.refresh(context["inventory"])

    # Since the returned item is not put back into inventory,
    # inventory remains at the post-sale quantity.
    assert context["inventory"].quantity_on_hand == 6


def test_process_sales_return_api_rejects_empty_return(
    client,
    db,
):
    context = create_sales_return_api_context(db)

    response = create_sales_return(client, context)

    return_id = response.json()["return_id"]

    response = client.post(
        f"/sales-returns/{return_id}/process",
        headers=auth_headers(context["token"]),
        json={
            "refund_method": "cash",
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"] == (
        "Sales return must contain at least one item."
    )


def test_get_sales_return_api(client, db):
    context = create_sales_return_api_context(db)

    response = create_sales_return(client, context)

    return_id = response.json()["return_id"]

    response = client.get(
        f"/sales-returns/{return_id}",
        headers=auth_headers(context["token"]),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["return_id"] == return_id
    assert data["status"] == "requested"
    assert data["items"] == []


def test_get_sales_return_api_returns_404_for_unknown_return(
    client,
    db,
):
    context = create_sales_return_api_context(db)

    response = client.get(
        "/sales-returns/SR-DOES-NOT-EXIST",
        headers=auth_headers(context["token"]),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Sales return not found."


def test_process_sales_return_api_rejects_second_processing(
    client,
    db,
):
    context = create_sales_return_api_context(db)

    response = create_sales_return(client, context)

    return_id = response.json()["return_id"]

    item_response = client.post(
        f"/sales-returns/{return_id}/items",
        headers=auth_headers(context["token"]),
        json={
            "invoice_item_id": str(
                context["invoice_item"].id
            ),
            "quantity": 1,
            "condition": "good",
            "return_to_inventory": True,
            "restocking_fee": "0.00",
        },
    )

    assert item_response.status_code == 200

    response = client.post(
        f"/sales-returns/{return_id}/process",
        headers=auth_headers(context["token"]),
        json={
            "refund_method": "cash",
        },
    )

    assert response.status_code == 200

    response = client.post(
        f"/sales-returns/{return_id}/process",
        headers=auth_headers(context["token"]),
        json={
            "refund_method": "cash",
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"] == (
        "Only requested sales returns can be processed."
    )


def test_create_sales_return_api_rejects_duplicate_requested_return(
    client,
    db,
):
    context = create_sales_return_api_context(db)

    first_response = create_sales_return(client, context)

    assert first_response.status_code == 201

    response = client.post(
        "/sales-returns",
        headers=auth_headers(context["token"]),
        json={
            "invoice_id": context["invoice"].invoice_id,
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"] == (
        "A requested sales return already exists for this invoice."
    )


def test_add_sales_return_item_api_unknown_return(
    client,
    db,
):
    context = create_sales_return_api_context(db)

    response = client.post(
        "/sales-returns/SR-DOES-NOT-EXIST/items",
        headers=auth_headers(context["token"]),
        json={
            "invoice_item_id": str(context["invoice_item"].id),
            "quantity": 1,
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Sales return not found."


def test_process_sales_return_api_unknown_return(
    client,
    db,
):
    context = create_sales_return_api_context(db)

    response = client.post(
        "/sales-returns/SR-DOES-NOT-EXIST/process",
        headers=auth_headers(context["token"]),
        json={
            "refund_method": "cash",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Sales return not found."


def test_add_sales_return_item_api_rejects_invalid_condition(
    client,
    db,
):
    context = create_sales_return_api_context(db)

    response = create_sales_return(client, context)

    return_id = response.json()["return_id"]

    response = client.post(
        f"/sales-returns/{return_id}/items",
        headers=auth_headers(context["token"]),
        json={
            "invoice_item_id": str(context["invoice_item"].id),
            "quantity": 1,
            "condition": "unknown_condition",
            "return_to_inventory": True,
            "restocking_fee": "0.00",
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"] == (
        "Invalid return condition."
    )


def test_add_sales_return_item_api_rejects_excess_restocking_fee(
    client,
    db,
):
    context = create_sales_return_api_context(db)

    response = create_sales_return(client, context)

    return_id = response.json()["return_id"]

    response = client.post(
        f"/sales-returns/{return_id}/items",
        headers=auth_headers(context["token"]),
        json={
            "invoice_item_id": str(context["invoice_item"].id),
            "quantity": 1,
            "condition": "good",
            "return_to_inventory": True,
            "restocking_fee": "1500.01",
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"] == (
        "Restocking fee cannot exceed return amount."
    )


def test_add_sales_return_item_api_rejects_negative_restocking_fee(
    client,
    db,
):
    context = create_sales_return_api_context(db)

    response = create_sales_return(client, context)

    return_id = response.json()["return_id"]

    response = client.post(
        f"/sales-returns/{return_id}/items",
        headers=auth_headers(context["token"]),
        json={
            "invoice_item_id": str(context["invoice_item"].id),
            "quantity": 1,
            "condition": "good",
            "return_to_inventory": True,
            "restocking_fee": "-1.00",
        },
    )

    # Pydantic validates the request before the service is called.
    assert response.status_code == 422


def test_add_sales_return_item_api_rejects_item_from_wrong_invoice(
    client,
    db,
):
    context = create_sales_return_api_context(db)

    other_invoice = create_invoice(
        db=db,
        retailer=context["retailer"],
        customer=context["customer"],
        location=context["location"],
        items=[
            InvoiceItemCreateRequest(
                sku=context["variant"].sku,
                quantity=1,
            )
        ],
    )

    other_invoice_item = other_invoice.items[0]

    response = create_sales_return(client, context)

    return_id = response.json()["return_id"]

    response = client.post(
        f"/sales-returns/{return_id}/items",
        headers=auth_headers(context["token"]),
        json={
            "invoice_item_id": str(other_invoice_item.id),
            "quantity": 1,
            "condition": "good",
            "return_to_inventory": True,
            "restocking_fee": "0.00",
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"] == (
        "Invoice item does not belong to this invoice."
    )


def test_add_sales_return_item_api_rejects_after_processing(
    client,
    db,
):
    context = create_sales_return_api_context(db)

    response = create_sales_return(client, context)

    return_id = response.json()["return_id"]

    item_response = client.post(
        f"/sales-returns/{return_id}/items",
        headers=auth_headers(context["token"]),
        json={
            "invoice_item_id": str(context["invoice_item"].id),
            "quantity": 1,
            "condition": "good",
            "return_to_inventory": True,
            "restocking_fee": "0.00",
        },
    )

    assert item_response.status_code == 200

    process_response = client.post(
        f"/sales-returns/{return_id}/process",
        headers=auth_headers(context["token"]),
        json={
            "refund_method": "cash",
        },
    )

    assert process_response.status_code == 200

    response = client.post(
        f"/sales-returns/{return_id}/items",
        headers=auth_headers(context["token"]),
        json={
            "invoice_item_id": str(context["invoice_item"].id),
            "quantity": 1,
            "condition": "good",
            "return_to_inventory": True,
            "restocking_fee": "0.00",
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"] == (
        "Items can only be added to a requested sales return."
    )


def test_create_sales_return_api_requires_authentication(
    client,
    db,
):
    context = create_sales_return_api_context(db)

    response = client.post(
        "/sales-returns",
        json={
            "invoice_id": context["invoice"].invoice_id,
        },
    )

    assert response.status_code in (401, 403)


def test_get_sales_return_api_requires_authentication(
    client,
    db,
):
    context = create_sales_return_api_context(db)

    response = create_sales_return(client, context)

    return_id = response.json()["return_id"]

    response = client.get(
        f"/sales-returns/{return_id}",
    )

    assert response.status_code in (401, 403)
