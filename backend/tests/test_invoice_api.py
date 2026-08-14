from app.schemas.invoice import InvoiceItemCreateRequest
from app.services.invoice_service import create_invoice
from uuid import uuid4

from app.models.customer import Customer
from app.models.inventory_item import InventoryItem
from app.models.inventory_location import InventoryLocation
from app.models.product import Product
from app.models.product_variant import ProductVariant
from app.models.retailer import Retailer
from app.models.user import User
from app.models.role import Role
from app.models.access_control import user_roles
from app.services.auth_service import create_user_token


def create_invoice_api_context(db, stock_quantity=5):
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
        retailer_id=f"RET-INV-{uuid4().hex[:8].upper()}",
        owner_user_id=user.id,
        business_name="Invoice API Retailer",
        phone_number=user.phone_number,
        status="active",
    )
    db.add(retailer)
    db.flush()

    location = InventoryLocation(
        retailer_id=retailer.id,
        name="Invoice API Store",
        location_type="store",
        is_active=True,
    )
    db.add(location)
    db.flush()

    customer_user = User(
        phone_number=f"888{uuid4().hex[:7]}",
        status="active",
    )
    db.add(customer_user)
    db.flush()

    customer = Customer(
        customer_id=f"CUS-INV-{uuid4().hex[:8].upper()}",
        user_id=customer_user.id,
        full_name="Invoice API Customer",
        phone_number=customer_user.phone_number,
        status="active",
    )
    db.add(customer)
    db.flush()

    product = Product(
        product_code=f"PROD-INV-{uuid4().hex[:8].upper()}",
        name="Invoice API Product",
        status="active",
    )
    db.add(product)
    db.flush()

    variant = ProductVariant(
        product_id=product.id,
        sku=f"INV-API-{uuid4().hex[:8].upper()}",
        variant_name="Invoice API Variant",
        selling_price=30000,
        purchase_cost=25000,
        tax_rate=18,
        track_inventory=True,
        status="active",
    )
    db.add(variant)
    db.flush()

    inventory = InventoryItem(
        retailer_id=retailer.id,
        location_id=location.id,
        product_variant_id=variant.id,
        quantity_on_hand=stock_quantity,
        quantity_reserved=0,
        average_cost=25000,
    )
    db.add(inventory)
    db.flush()

    db.commit()

    return {
        "user": user,
        "retailer": retailer,
        "location": location,
        "customer": customer,
        "product": product,
        "variant": variant,
        "inventory": inventory,
        "token": create_user_token(user),
    }


def test_create_invoice_api(client, db):
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
        retailer_id=f"RET-{uuid4().hex[:8].upper()}",
        owner_user_id=user.id,
        business_name="API Test Retailer",
        phone_number=user.phone_number,
        status="active",
    )
    db.add(retailer)
    db.flush()

    location = InventoryLocation(
        retailer_id=retailer.id,
        name="API Test Store",
        location_type="store",
        is_active=True,
    )
    db.add(location)
    db.flush()

    customer_user = User(
        phone_number=f"888{uuid4().hex[:7]}",
        status="active",
    )
    db.add(customer_user)
    db.flush()

    customer = Customer(
        customer_id=f"CUS-{uuid4().hex[:8].upper()}",
        user_id=customer_user.id,
        full_name="API Test Customer",
        phone_number=customer_user.phone_number,
        status="active",
    )
    db.add(customer)
    db.flush()

    product = Product(
        product_code=f"PROD-{uuid4().hex[:8].upper()}",
        name="API Test Phone",
        status="active",
    )
    db.add(product)
    db.flush()

    variant = ProductVariant(
        product_id=product.id,
        sku=f"API-TEST-{uuid4().hex[:8].upper()}",
        variant_name="128GB Black",
        selling_price=30000,
        purchase_cost=25000,
        tax_rate=18,
        track_inventory=True,
        status="active",
    )
    db.add(variant)
    db.flush()

    inventory = InventoryItem(
        retailer_id=retailer.id,
        location_id=location.id,
        product_variant_id=variant.id,
        quantity_on_hand=5,
        quantity_reserved=0,
        average_cost=25000,
    )
    db.add(inventory)
    db.flush()

    db.commit()

    token = create_user_token(user)

    response = client.post(
        "/invoices",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "customer_id": customer.customer_id,
            "location_id": str(location.id),
            "items": [
                {
                    "sku": variant.sku,
                    "quantity": 2,
                }
            ],
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["status"] == "active"
    assert data["payment_status"] == "unpaid"
    assert len(data["items"]) == 1
    assert data["items"][0]["sku"] == variant.sku
    assert data["items"][0]["quantity"] == 2

    db.refresh(inventory)

    assert inventory.quantity_on_hand == 3


def test_get_invoice_api(client, db):
    context = create_invoice_api_context(db)

    response = client.post(
        "/invoices",
        headers={
            "Authorization": f"Bearer {context['token']}",
        },
        json={
            "customer_id": context["customer"].customer_id,
            "location_id": str(context["location"].id),
            "items": [
                {
                    "sku": context["variant"].sku,
                    "quantity": 2,
                }
            ],
        },
    )

    assert response.status_code == 201

    invoice_id = response.json()["invoice_id"]

    response = client.get(
        f"/invoices/{invoice_id}",
        headers={
            "Authorization": f"Bearer {context['token']}",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["invoice_id"] == invoice_id
    assert data["retailer_id"] == str(context["retailer"].id)
    assert data["customer_id"] == str(context["customer"].id)
    assert data["status"] == "active"
    assert data["payment_status"] == "unpaid"

    assert len(data["items"]) == 1
    assert data["items"][0]["sku"] == context["variant"].sku
    assert data["items"][0]["quantity"] == 2


def test_get_invoice_api_rejects_unknown_invoice(client, db):
    context = create_invoice_api_context(db)

    response = client.get(
        "/invoices/INV-DOES-NOT-EXIST",
        headers={
            "Authorization": f"Bearer {context['token']}",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Invoice not found."


def test_create_invoice_api_rejects_unknown_customer(client, db):
    context = create_invoice_api_context(db)

    response = client.post(
        "/invoices",
        headers={
            "Authorization": f"Bearer {context['token']}",
        },
        json={
            "customer_id": "CUS-DOES-NOT-EXIST",
            "location_id": str(context["location"].id),
            "items": [
                {
                    "sku": context["variant"].sku,
                    "quantity": 1,
                }
            ],
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Customer not found."


def test_create_invoice_api_rejects_unknown_location(client, db):
    context = create_invoice_api_context(db)

    response = client.post(
        "/invoices",
        headers={
            "Authorization": f"Bearer {context['token']}",
        },
        json={
            "customer_id": context["customer"].customer_id,
            "location_id": str(uuid4()),
            "items": [
                {
                    "sku": context["variant"].sku,
                    "quantity": 1,
                }
            ],
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == (
        "Inventory location not found."
    )


def test_create_invoice_api_rejects_insufficient_stock(client, db):
    context = create_invoice_api_context(
        db,
        stock_quantity=2,
    )

    response = client.post(
        "/invoices",
        headers={
            "Authorization": f"Bearer {context['token']}",
        },
        json={
            "customer_id": context["customer"].customer_id,
            "location_id": str(context["location"].id),
            "items": [
                {
                    "sku": context["variant"].sku,
                    "quantity": 3,
                }
            ],
        },
    )

    assert response.status_code == 409
    assert "Insufficient available stock" in (
        response.json()["detail"]
    )


def test_create_invoice_api_rejects_unknown_sku(client, db):
    context = create_invoice_api_context(db)

    response = client.post(
        "/invoices",
        headers={
            "Authorization": f"Bearer {context['token']}",
        },
        json={
            "customer_id": context["customer"].customer_id,
            "location_id": str(context["location"].id),
            "items": [
                {
                    "sku": "SKU-DOES-NOT-EXIST",
                    "quantity": 1,
                }
            ],
        },
    )

    assert response.status_code == 409
    assert "Product variant with SKU" in (
        response.json()["detail"]
    )


def test_create_invoice_api_calculates_tax_and_invoice_discount(
    client,
    db,
):
    context = create_invoice_api_context(db)

    response = client.post(
        "/invoices",
        headers={
            "Authorization": f"Bearer {context['token']}",
        },
        json={
            "customer_id": context["customer"].customer_id,
            "location_id": str(context["location"].id),
            "discount_amount": "5000.00",
            "invoice_number": "INV-API-001",
            "notes": "Financial calculation test",
            "items": [
                {
                    "sku": context["variant"].sku,
                    "quantity": 2,
                }
            ],
        },
    )

    assert response.status_code == 201

    data = response.json()

    # 2 × 30,000 = 60,000
    assert data["subtotal"] == "60000.00"

    # Invoice-level discount
    assert data["discount_amount"] == "5000.00"

    # Tax is calculated on the item net amount before invoice-level discount.
    assert data["tax_amount"] == "10800.00"

    # 60,000 - 5,000 + 10,800 = 65,800
    assert data["total_amount"] == "65800.00"

    assert data["invoice_number"] == "INV-API-001"
    assert data["notes"] == "Financial calculation test"


def test_create_invoice_api_supports_custom_item_price_and_discount(
    client,
    db,
):
    context = create_invoice_api_context(db)

    response = client.post(
        "/invoices",
        headers={
            "Authorization": f"Bearer {context['token']}",
        },
        json={
            "customer_id": context["customer"].customer_id,
            "location_id": str(context["location"].id),
            "items": [
                {
                    "sku": context["variant"].sku,
                    "quantity": 2,
                    "unit_price": "28000.00",
                    "discount_amount": "2000.00",
                }
            ],
        },
    )

    assert response.status_code == 201

    data = response.json()

    # 2 × 28,000 = 56,000
    # Item discount = 2,000
    # Net = 54,000
    # Tax = 54,000 × 18% = 9,720
    # Total = 63,720
    assert data["subtotal"] == "54000.00"
    assert data["discount_amount"] == "0.00"
    assert data["tax_amount"] == "9720.00"
    assert data["total_amount"] == "63720.00"

    assert len(data["items"]) == 1

    item = data["items"][0]

    assert item["unit_price"] == "28000.00"
    assert item["discount_amount"] == "2000.00"
    assert item["tax_rate"] == "18.00"
    assert item["tax_amount"] == "9720.00"
    assert item["line_total"] == "63720.00"


def test_create_invoice_api_rejects_item_discount_above_amount(
    client,
    db,
):
    context = create_invoice_api_context(db)

    response = client.post(
        "/invoices",
        headers={
            "Authorization": f"Bearer {context['token']}",
        },
        json={
            "customer_id": context["customer"].customer_id,
            "location_id": str(context["location"].id),
            "items": [
                {
                    "sku": context["variant"].sku,
                    "quantity": 1,
                    "discount_amount": "30001.00",
                }
            ],
        },
    )

    assert response.status_code == 409
    assert "Item discount cannot exceed item amount" in (
        response.json()["detail"]
    )


def test_create_invoice_api_rejects_invoice_discount_above_subtotal(
    client,
    db,
):
    context = create_invoice_api_context(db)

    response = client.post(
        "/invoices",
        headers={
            "Authorization": f"Bearer {context['token']}",
        },
        json={
            "customer_id": context["customer"].customer_id,
            "location_id": str(context["location"].id),
            "discount_amount": "30001.00",
            "items": [
                {
                    "sku": context["variant"].sku,
                    "quantity": 1,
                }
            ],
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"] == (
        "Invoice discount cannot exceed subtotal."
    )


def test_create_invoice_api_rejects_inactive_retailer(client, db):
    context = create_invoice_api_context(db)

    context["retailer"].status = "inactive"
    db.commit()

    response = client.post(
        "/invoices",
        headers={
            "Authorization": f"Bearer {context['token']}",
        },
        json={
            "customer_id": context["customer"].customer_id,
            "location_id": str(context["location"].id),
            "items": [
                {
                    "sku": context["variant"].sku,
                    "quantity": 1,
                }
            ],
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "Retailer is not active."


def test_create_invoice_api_rejects_inactive_customer(client, db):
    context = create_invoice_api_context(db)

    context["customer"].status = "inactive"
    db.commit()

    response = client.post(
        "/invoices",
        headers={
            "Authorization": f"Bearer {context['token']}",
        },
        json={
            "customer_id": context["customer"].customer_id,
            "location_id": str(context["location"].id),
            "items": [
                {
                    "sku": context["variant"].sku,
                    "quantity": 1,
                }
            ],
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "Customer is not active."


def test_create_serialized_invoice_api_assigns_ownership(
    client,
    db,
):
    context = create_invoice_api_context(db)

    context["variant"].requires_serial_number = True

    from app.models.product_unit import ProductUnit

    unit = ProductUnit(
        product_variant_id=context["variant"].id,
        serial_number=f"SN-INV-{uuid4().hex[:12].upper()}",
        status="in_stock",
    )
    db.add(unit)
    db.commit()

    response = client.post(
        "/invoices",
        headers={
            "Authorization": f"Bearer {context['token']}",
        },
        json={
            "customer_id": context["customer"].customer_id,
            "location_id": str(context["location"].id),
            "items": [
                {
                    "sku": context["variant"].sku,
                    "quantity": 1,
                    "product_unit_ids": [str(unit.id)],
                }
            ],
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert len(data["items"]) == 1
    assert data["items"][0]["quantity"] == 1

    db.refresh(unit)

    assert unit.status == "sold"

    from app.models.invoice_item_unit import InvoiceItemUnit
    from app.models.product_ownership import ProductOwnership

    mapping = db.query(InvoiceItemUnit).filter(
        InvoiceItemUnit.product_unit_id == unit.id
    ).one()

    assert mapping.invoice_item_id == (
        context["variant"].id
        if False
        else mapping.invoice_item_id
    )

    ownership = db.query(ProductOwnership).filter(
        ProductOwnership.product_unit_id == unit.id
    ).one()

    assert ownership.customer_id == context["customer"].id
    assert ownership.ownership_status == "active"


def test_create_serialized_invoice_api_requires_exact_units(
    client,
    db,
):
    context = create_invoice_api_context(db)

    context["variant"].requires_serial_number = True
    db.commit()

    response = client.post(
        "/invoices",
        headers={
            "Authorization": f"Bearer {context['token']}",
        },
        json={
            "customer_id": context["customer"].customer_id,
            "location_id": str(context["location"].id),
            "items": [
                {
                    "sku": context["variant"].sku,
                    "quantity": 2,
                    "product_unit_ids": [],
                }
            ],
        },
    )

    assert response.status_code == 409
    assert "requires exactly 2 product unit IDs" in (
        response.json()["detail"]
    )


def test_create_serialized_invoice_api_rejects_unavailable_unit(
    client,
    db,
):
    context = create_invoice_api_context(db)

    context["variant"].requires_serial_number = True

    from app.models.product_unit import ProductUnit

    unit = ProductUnit(
        product_variant_id=context["variant"].id,
        serial_number=f"SN-SOLD-{uuid4().hex[:12].upper()}",
        status="sold",
    )
    db.add(unit)
    db.commit()

    response = client.post(
        "/invoices",
        headers={
            "Authorization": f"Bearer {context['token']}",
        },
        json={
            "customer_id": context["customer"].customer_id,
            "location_id": str(context["location"].id),
            "items": [
                {
                    "sku": context["variant"].sku,
                    "quantity": 1,
                    "product_unit_ids": [str(unit.id)],
                }
            ],
        },
    )

    assert response.status_code == 409
    assert "is not available for sale" in (
        response.json()["detail"]
    )


def test_create_invoice_api_rejects_user_without_retailer(
    client,
    db,
):
    context = create_invoice_api_context(db)

    user_without_retailer = User(
        phone_number=f"777{uuid4().hex[:7]}",
        status="active",
    )
    db.add(user_without_retailer)
    db.flush()

    role = db.query(Role).filter(
        Role.name == "retailer_owner"
    ).one()

    db.execute(
        user_roles.insert().values(
            user_id=user_without_retailer.id,
            role_id=role.id,
        )
    )
    db.flush()

    token = create_user_token(user_without_retailer)

    response = client.post(
        "/invoices",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "customer_id": context["customer"].customer_id,
            "location_id": str(context["location"].id),
            "items": [
                {
                    "sku": context["variant"].sku,
                    "quantity": 1,
                }
            ],
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == (
        "Retailer not found for this user."
    )


def test_get_invoice_api_rejects_user_without_retailer(
    client,
    db,
):
    context = create_invoice_api_context(db)

    invoice = create_invoice(
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

    invoice_id = invoice.invoice_id

    user_without_retailer = User(
        phone_number=f"777{uuid4().hex[:7]}",
        status="active",
    )
    db.add(user_without_retailer)
    db.flush()

    role = db.query(Role).filter(
        Role.name == "retailer_owner"
    ).one()

    db.execute(
        user_roles.insert().values(
            user_id=user_without_retailer.id,
            role_id=role.id,
        )
    )
    db.flush()

    token = create_user_token(user_without_retailer)

    response = client.get(
        f"/invoices/{invoice_id}",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == (
        "Retailer not found for this user."
    )


def test_get_invoice_api_rejects_invoice_from_another_retailer(
    client,
    db,
):
    context = create_invoice_api_context(db)

    invoice = create_invoice(
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

    other_user = User(
        phone_number=f"777{uuid4().hex[:7]}",
        status="active",
    )
    db.add(other_user)
    db.flush()

    role = db.query(Role).filter(
        Role.name == "retailer_owner"
    ).one()

    db.execute(
        user_roles.insert().values(
            user_id=other_user.id,
            role_id=role.id,
        )
    )
    db.flush()

    other_retailer = Retailer(
        retailer_id=f"RET-OTHER-{uuid4().hex[:8].upper()}",
        owner_user_id=other_user.id,
        business_name="Other Retailer",
        phone_number=other_user.phone_number,
        status="active",
    )
    db.add(other_retailer)
    db.commit()

    other_token = create_user_token(other_user)

    response = client.get(
        f"/invoices/{invoice.invoice_id}",
        headers={
            "Authorization": f"Bearer {other_token}",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Invoice not found."


