from datetime import date, timedelta
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


def create_warranty_api_context(db):
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
        retailer_id=f"RET-WAR-API-{uuid4().hex[:6].upper()}",
        owner_user_id=user.id,
        business_name="Warranty API Retailer",
        phone_number=user.phone_number,
        status="active",
    )
    db.add(retailer)
    db.flush()

    location = InventoryLocation(
        retailer_id=retailer.id,
        name="Warranty API Store",
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
        customer_id=f"CUS-WAR-API-{uuid4().hex[:6].upper()}",
        user_id=customer_user.id,
        full_name="Warranty API Customer",
        phone_number=customer_user.phone_number,
        status="active",
    )
    db.add(customer)
    db.flush()

    second_customer_user = User(
        phone_number=f"9{uuid4().hex[:9]}",
        status="active",
    )
    db.add(second_customer_user)
    db.flush()

    second_customer = Customer(
        customer_id=f"CUS-WAR-API-2-{uuid4().hex[:6].upper()}",
        user_id=second_customer_user.id,
        full_name="Second Warranty Customer",
        phone_number=second_customer_user.phone_number,
        status="active",
    )
    db.add(second_customer)
    db.flush()

    product = Product(
        product_code=f"PROD-WAR-API-{uuid4().hex[:6].upper()}",
        name="Warranty API Product",
        status="active",
    )
    db.add(product)
    db.flush()

    variant = ProductVariant(
        product_id=product.id,
        sku=f"SKU-WAR-API-{uuid4().hex[:6].upper()}",
        variant_name="Warranty API Variant",
        selling_price=Decimal("5000.00"),
        purchase_cost=Decimal("3500.00"),
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
        average_cost=Decimal("3500.00"),
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
                quantity=2,
            )
        ],
    )

    db.refresh(invoice)

    return {
        "user": user,
        "retailer": retailer,
        "location": location,
        "customer": customer,
        "second_customer": second_customer,
        "product": product,
        "variant": variant,
        "inventory": inventory,
        "invoice": invoice,
        "token": token,
    }


def auth_headers(token):
    return {
        "Authorization": f"Bearer {token}",
    }


def create_warranty(client, context, transferable=True):
    start_date = date.today()
    end_date = start_date + timedelta(days=365)

    response = client.post(
        "/warranties",
        headers=auth_headers(context["token"]),
        json={
            "invoice_id": context["invoice"].invoice_id,
            "product_variant_id": str(context["variant"].id),
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "duration_months": 12,
            "is_transferable": transferable,
        },
    )

    assert response.status_code == 201

    return response


def test_create_warranty_api(client, db):
    context = create_warranty_api_context(db)

    response = create_warranty(client, context)

    data = response.json()

    assert data["invoice_id"] == str(context["invoice"].id)
    assert data["product_variant_id"] == str(
        context["variant"].id
    )
    assert data["customer_id"] == str(
        context["customer"].id
    )
    assert data["start_date"] == date.today().isoformat()
    assert data["end_date"] == (
        date.today() + timedelta(days=365)
    ).isoformat()
    assert data["duration_months"] == 12
    assert data["is_transferable"] is True
    assert data["status"] == "active"
    assert data["warranty_id"].startswith("WAR-")
    assert data["id"]


def test_create_warranty_api_rejects_unknown_invoice(
    client,
    db,
):
    context = create_warranty_api_context(db)

    response = client.post(
        "/warranties",
        headers=auth_headers(context["token"]),
        json={
            "invoice_id": "INV-DOES-NOT-EXIST",
            "product_variant_id": str(context["variant"].id),
            "start_date": date.today().isoformat(),
            "end_date": (
                date.today() + timedelta(days=365)
            ).isoformat(),
            "duration_months": 12,
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Invoice not found."


def test_create_warranty_api_rejects_unknown_product_variant(
    client,
    db,
):
    context = create_warranty_api_context(db)

    response = client.post(
        "/warranties",
        headers=auth_headers(context["token"]),
        json={
            "invoice_id": context["invoice"].invoice_id,
            "product_variant_id": str(uuid4()),
            "start_date": date.today().isoformat(),
            "end_date": (
                date.today() + timedelta(days=365)
            ).isoformat(),
            "duration_months": 12,
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "Product variant not found."


def test_create_warranty_api_rejects_variant_not_sold_on_invoice(
    client,
    db,
):
    context = create_warranty_api_context(db)

    other_product = Product(
        product_code=f"PROD-OTHER-{uuid4().hex[:8].upper()}",
        name="Other Product",
        status="active",
    )
    db.add(other_product)
    db.flush()

    other_variant = ProductVariant(
        product_id=other_product.id,
        sku=f"SKU-OTHER-{uuid4().hex[:8].upper()}",
        variant_name="Other Variant",
        selling_price=Decimal("1000.00"),
        purchase_cost=Decimal("700.00"),
        tax_rate=Decimal("18.00"),
        track_inventory=True,
        status="active",
    )
    db.add(other_variant)
    db.commit()

    response = client.post(
        "/warranties",
        headers=auth_headers(context["token"]),
        json={
            "invoice_id": context["invoice"].invoice_id,
            "product_variant_id": str(other_variant.id),
            "start_date": date.today().isoformat(),
            "end_date": (
                date.today() + timedelta(days=365)
            ).isoformat(),
            "duration_months": 12,
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"] == (
        "Product variant was not sold on this invoice."
    )


def test_create_warranty_api_rejects_invalid_date_range(
    client,
    db,
):
    context = create_warranty_api_context(db)

    start_date = date.today()
    end_date = start_date - timedelta(days=1)

    response = client.post(
        "/warranties",
        headers=auth_headers(context["token"]),
        json={
            "invoice_id": context["invoice"].invoice_id,
            "product_variant_id": str(context["variant"].id),
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "duration_months": 12,
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"] == (
        "Warranty start date cannot be after end date."
    )


def test_create_warranty_api_rejects_duplicate_active_warranty(
    client,
    db,
):
    context = create_warranty_api_context(db)

    create_warranty(client, context)

    response = client.post(
        "/warranties",
        headers=auth_headers(context["token"]),
        json={
            "invoice_id": context["invoice"].invoice_id,
            "product_variant_id": str(context["variant"].id),
            "start_date": date.today().isoformat(),
            "end_date": (
                date.today() + timedelta(days=365)
            ).isoformat(),
            "duration_months": 12,
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"] == (
        "An active warranty already exists for this invoice item."
    )


def test_get_warranty_api(client, db):
    context = create_warranty_api_context(db)

    create_response = create_warranty(client, context)

    warranty_id = create_response.json()["warranty_id"]

    response = client.get(
        f"/warranties/{warranty_id}",
        headers=auth_headers(context["token"]),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["warranty_id"] == warranty_id
    assert data["invoice_id"] == str(context["invoice"].id)
    assert data["product_variant_id"] == str(
        context["variant"].id
    )
    assert data["customer_id"] == str(
        context["customer"].id
    )
    assert data["status"] == "active"


def test_get_warranty_api_returns_404_for_unknown_warranty(
    client,
    db,
):
    context = create_warranty_api_context(db)

    response = client.get(
        "/warranties/WAR-DOES-NOT-EXIST",
        headers=auth_headers(context["token"]),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Warranty not found."


def test_update_warranty_status_api(client, db):
    context = create_warranty_api_context(db)

    create_response = create_warranty(client, context)

    warranty_id = create_response.json()["warranty_id"]

    response = client.post(
        f"/warranties/{warranty_id}/status",
        headers=auth_headers(context["token"]),
        json={
            "status": "expired",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["warranty_id"] == warranty_id
    assert data["status"] == "expired"


def test_update_warranty_status_api_rejects_invalid_status(
    client,
    db,
):
    context = create_warranty_api_context(db)

    create_response = create_warranty(client, context)

    warranty_id = create_response.json()["warranty_id"]

    response = client.post(
        f"/warranties/{warranty_id}/status",
        headers=auth_headers(context["token"]),
        json={
            "status": "invalid",
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "Invalid warranty status."


def test_update_cancelled_warranty_api_cannot_reactivate(
    client,
    db,
):
    context = create_warranty_api_context(db)

    create_response = create_warranty(client, context)

    warranty_id = create_response.json()["warranty_id"]

    cancel_response = client.post(
        f"/warranties/{warranty_id}/status",
        headers=auth_headers(context["token"]),
        json={
            "status": "cancelled",
        },
    )

    assert cancel_response.status_code == 200

    response = client.post(
        f"/warranties/{warranty_id}/status",
        headers=auth_headers(context["token"]),
        json={
            "status": "active",
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"] == (
        "A cancelled warranty cannot be reactivated."
    )


def test_transfer_warranty_api(client, db):
    context = create_warranty_api_context(db)

    create_response = create_warranty(client, context)

    warranty_id = create_response.json()["warranty_id"]

    response = client.post(
        f"/warranties/{warranty_id}/transfer",
        headers=auth_headers(context["token"]),
        json={
            "customer_id": str(context["second_customer"].id),
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["warranty_id"] == warranty_id
    assert data["customer_id"] == str(
        context["second_customer"].id
    )
    assert data["status"] == "active"


def test_transfer_warranty_api_rejects_non_transferable_warranty(
    client,
    db,
):
    context = create_warranty_api_context(db)

    create_response = create_warranty(
        client,
        context,
        transferable=False,
    )

    warranty_id = create_response.json()["warranty_id"]

    response = client.post(
        f"/warranties/{warranty_id}/transfer",
        headers=auth_headers(context["token"]),
        json={
            "customer_id": str(context["second_customer"].id),
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"] == (
        "This warranty is not transferable."
    )


def test_transfer_warranty_api_rejects_unknown_customer(
    client,
    db,
):
    context = create_warranty_api_context(db)

    create_response = create_warranty(client, context)

    warranty_id = create_response.json()["warranty_id"]

    response = client.post(
        f"/warranties/{warranty_id}/transfer",
        headers=auth_headers(context["token"]),
        json={
            "customer_id": str(uuid4()),
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "Customer not found."


def test_transfer_warranty_api_rejects_invalid_customer_id(
    client,
    db,
):
    context = create_warranty_api_context(db)

    create_response = create_warranty(client, context)

    warranty_id = create_response.json()["warranty_id"]

    response = client.post(
        f"/warranties/{warranty_id}/transfer",
        headers=auth_headers(context["token"]),
        json={
            "customer_id": "not-a-uuid",
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "Invalid customer ID."


def test_transfer_warranty_api_rejects_same_customer(
    client,
    db,
):
    context = create_warranty_api_context(db)

    create_response = create_warranty(client, context)

    warranty_id = create_response.json()["warranty_id"]

    response = client.post(
        f"/warranties/{warranty_id}/transfer",
        headers=auth_headers(context["token"]),
        json={
            "customer_id": str(context["customer"].id),
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"] == (
        "Warranty already belongs to this customer."
    )
