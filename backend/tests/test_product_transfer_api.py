from decimal import Decimal
import uuid

from app.models.access_control import user_roles
from app.models.customer import Customer
from app.models.invoice import Invoice
from app.models.invoice_item import InvoiceItem
from app.models.product import Product
from app.models.product_ownership import ProductOwnership
from app.models.product_unit import ProductUnit
from app.models.product_variant import ProductVariant
from app.models.retailer import Retailer
from app.models.role import Role
from app.models.user import User
from app.services.auth_service import create_user_token
from app.services.product_ownership_service import assign_product_ownership


def create_customer(db, name):
    user = User(
        phone_number=f"9{uuid.uuid4().hex[:9]}",
        status="active",
    )
    db.add(user)
    db.flush()

    customer = Customer(
        customer_id=f"CUS-{uuid.uuid4().hex[:8].upper()}",
        user_id=user.id,
        full_name=name,
        phone_number=user.phone_number,
        status="active",
    )
    db.add(customer)
    db.flush()

    return customer


def create_product_unit(db):
    product = Product(
        product_code=f"PROD-TRF-API-{uuid.uuid4().hex[:6].upper()}",
        name="Transfer API Product",
        status="active",
    )
    db.add(product)
    db.flush()

    variant = ProductVariant(
        product_id=product.id,
        sku=f"SKU-TRF-API-{uuid.uuid4().hex[:6].upper()}",
        variant_name="Transfer API Variant",
        purchase_cost=Decimal("10000.00"),
        selling_price=Decimal("15000.00"),
        tax_rate=Decimal("18.00"),
        track_inventory=True,
        requires_serial_number=True,
        status="active",
    )
    db.add(variant)
    db.flush()

    unit = ProductUnit(
        product_variant_id=variant.id,
        serial_number=f"SN-TRF-API-{uuid.uuid4().hex[:8].upper()}",
        status="in_stock",
    )
    db.add(unit)
    db.flush()

    return product, variant, unit


def create_retailer_owner(db):
    user = User(
        phone_number=f"8{uuid.uuid4().hex[:9]}",
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
        retailer_id=f"RET-TRF-API-{uuid.uuid4().hex[:6].upper()}",
        owner_user_id=user.id,
        business_name="Product Transfer API Retailer",
        phone_number=user.phone_number,
        status="active",
    )
    db.add(retailer)
    db.flush()

    return user, retailer


def create_owned_product_unit(db, customer):
    product, variant, unit = create_product_unit(db)

    retailer_user, retailer = create_retailer_owner(db)

    invoice = Invoice(
        invoice_id=f"INV-TRF-API-{uuid.uuid4().hex[:8].upper()}",
        customer_id=customer.id,
        retailer_id=retailer.id,
        invoice_date=__import__("datetime").datetime.utcnow(),
        subtotal=Decimal("15000.00"),
        discount_amount=Decimal("0.00"),
        tax_amount=Decimal("2700.00"),
        total_amount=Decimal("17700.00"),
        payment_status="unpaid",
        status="active",
    )
    db.add(invoice)
    db.flush()

    invoice_item = InvoiceItem(
        invoice_id=invoice.id,
        product_variant_id=variant.id,
        product_name=product.name,
        sku=variant.sku,
        quantity=1,
        unit_price=Decimal("15000.00"),
        unit_cost=Decimal("10000.00"),
        discount_amount=Decimal("0.00"),
        tax_rate=Decimal("18.00"),
        tax_amount=Decimal("2700.00"),
        line_total=Decimal("17700.00"),
    )
    db.add(invoice_item)
    db.flush()

    assign_product_ownership(
        db=db,
        invoice=invoice,
        invoice_item=invoice_item,
        customer=customer,
        product_unit=unit,
    )

    db.commit()

    return {
        "product": product,
        "variant": variant,
        "unit": unit,
        "retailer_user": retailer_user,
        "retailer": retailer,
        "invoice": invoice,
        "invoice_item": invoice_item,
    }


def auth_headers(token):
    return {
        "Authorization": f"Bearer {token}",
    }


def create_transfer_context(db):
    owner_user, retailer = create_retailer_owner(db)

    source = create_customer(db, "Transfer Source")
    destination = create_customer(db, "Transfer Destination")

    product_context = create_owned_product_unit(
        db,
        source,
    )

    db.commit()

    return {
        "user": owner_user,
        "retailer": retailer,
        "source": source,
        "destination": destination,
        **product_context,
        "token": create_user_token(owner_user),
    }


def create_transfer(client, context, reason="Customer transfer"):
    response = client.post(
        "/product-transfers",
        headers=auth_headers(context["token"]),
        json={
            "product_unit_id": str(context["unit"].id),
            "from_customer_id": str(context["source"].id),
            "to_customer_id": str(context["destination"].id),
            "reason": reason,
        },
    )

    assert response.status_code == 201

    return response


def test_create_product_transfer_api(client, db):
    context = create_transfer_context(db)

    response = create_transfer(client, context)

    data = response.json()

    assert data["status"] == "pending"
    assert data["product_unit_id"] == str(context["unit"].id)
    assert data["from_customer_id"] == str(context["source"].id)
    assert data["to_customer_id"] == str(context["destination"].id)
    assert data["requested_by_user_id"] == str(context["user"].id)
    assert data["approved_by_user_id"] is None
    assert data["reason"] == "Customer transfer"
    assert data["rejection_reason"] is None
    assert data["approved_at"] is None
    assert data["completed_at"] is None
    assert data["transfer_id"].startswith("TRF-")


def test_get_product_transfer_api(client, db):
    context = create_transfer_context(db)

    create_response = create_transfer(client, context)
    transfer_id = create_response.json()["transfer_id"]

    response = client.get(
        f"/product-transfers/{transfer_id}",
        headers=auth_headers(context["token"]),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["transfer_id"] == transfer_id
    assert data["status"] == "pending"


def test_get_product_transfer_api_returns_404_for_unknown_transfer(
    client,
    db,
):
    context = create_transfer_context(db)

    response = client.get(
        "/product-transfers/TRF-DOES-NOT-EXIST",
        headers=auth_headers(context["token"]),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Product transfer not found."


def test_approve_product_transfer_api(client, db):
    context = create_transfer_context(db)

    create_response = create_transfer(client, context)
    transfer_id = create_response.json()["transfer_id"]

    response = client.post(
        f"/product-transfers/{transfer_id}/approve",
        headers=auth_headers(context["token"]),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "completed"
    assert data["approved_by_user_id"] == str(context["user"].id)
    assert data["approved_at"] is not None
    assert data["completed_at"] is not None


def test_approve_product_transfer_changes_ownership(
    client,
    db,
):
    context = create_transfer_context(db)

    create_response = create_transfer(client, context)
    transfer_id = create_response.json()["transfer_id"]

    response = client.post(
        f"/product-transfers/{transfer_id}/approve",
        headers=auth_headers(context["token"]),
    )

    assert response.status_code == 200

    ownerships = (
        db.query(ProductOwnership)
        .filter(
            ProductOwnership.product_unit_id == context["unit"].id
        )
        .all()
    )

    active = [
        ownership
        for ownership in ownerships
        if ownership.ownership_status == "active"
    ]

    released = [
        ownership
        for ownership in ownerships
        if ownership.ownership_status == "released"
    ]

    assert len(active) == 1
    assert active[0].customer_id == context["destination"].id

    assert len(released) == 1
    assert released[0].customer_id == context["source"].id


def test_reject_product_transfer_api(client, db):
    context = create_transfer_context(db)

    create_response = create_transfer(client, context)
    transfer_id = create_response.json()["transfer_id"]

    response = client.post(
        f"/product-transfers/{transfer_id}/reject",
        headers=auth_headers(context["token"]),
        json={
            "rejection_reason": "Transfer not authorized",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "rejected"
    assert data["rejection_reason"] == "Transfer not authorized"
    assert data["approved_by_user_id"] is None
    assert data["approved_at"] is None


def test_reject_product_transfer_does_not_change_ownership(
    client,
    db,
):
    context = create_transfer_context(db)

    create_response = create_transfer(client, context)
    transfer_id = create_response.json()["transfer_id"]

    response = client.post(
        f"/product-transfers/{transfer_id}/reject",
        headers=auth_headers(context["token"]),
        json={
            "rejection_reason": "Not authorized",
        },
    )

    assert response.status_code == 200

    ownership = (
        db.query(ProductOwnership)
        .filter(
            ProductOwnership.product_unit_id == context["unit"].id,
            ProductOwnership.ownership_status == "active",
        )
        .one()
    )

    assert ownership.customer_id == context["source"].id
    assert context["unit"].status == "sold"


def test_create_product_transfer_rejects_same_customer(
    client,
    db,
):
    context = create_transfer_context(db)

    response = client.post(
        "/product-transfers",
        headers=auth_headers(context["token"]),
        json={
            "product_unit_id": str(context["unit"].id),
            "from_customer_id": str(context["source"].id),
            "to_customer_id": str(context["source"].id),
        },
    )

    assert response.status_code == 409
    assert (
        response.json()["detail"]
        == "Source and destination customers must be different."
    )


def test_create_product_transfer_rejects_unknown_product_unit(
    client,
    db,
):
    context = create_transfer_context(db)

    response = client.post(
        "/product-transfers",
        headers=auth_headers(context["token"]),
        json={
            "product_unit_id": str(uuid.uuid4()),
            "from_customer_id": str(context["source"].id),
            "to_customer_id": str(context["destination"].id),
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Product unit not found."


def test_create_product_transfer_rejects_unknown_source_customer(
    client,
    db,
):
    context = create_transfer_context(db)

    response = client.post(
        "/product-transfers",
        headers=auth_headers(context["token"]),
        json={
            "product_unit_id": str(context["unit"].id),
            "from_customer_id": str(uuid.uuid4()),
            "to_customer_id": str(context["destination"].id),
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Source customer not found."


def test_create_product_transfer_rejects_unknown_destination_customer(
    client,
    db,
):
    context = create_transfer_context(db)

    response = client.post(
        "/product-transfers",
        headers=auth_headers(context["token"]),
        json={
            "product_unit_id": str(context["unit"].id),
            "from_customer_id": str(context["source"].id),
            "to_customer_id": str(uuid.uuid4()),
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Destination customer not found."


def test_create_product_transfer_rejects_duplicate_pending_transfer(
    client,
    db,
):
    context = create_transfer_context(db)

    create_transfer(client, context)

    response = client.post(
        "/product-transfers",
        headers=auth_headers(context["token"]),
        json={
            "product_unit_id": str(context["unit"].id),
            "from_customer_id": str(context["source"].id),
            "to_customer_id": str(context["destination"].id),
        },
    )

    assert response.status_code == 409
    assert (
        response.json()["detail"]
        == "This product unit already has a pending transfer."
    )


def test_create_product_transfer_rejects_unit_not_sold(
    client,
    db,
):
    context = create_transfer_context(db)

    context["unit"].status = "in_stock"
    db.commit()

    response = client.post(
        "/product-transfers",
        headers=auth_headers(context["token"]),
        json={
            "product_unit_id": str(context["unit"].id),
            "from_customer_id": str(context["source"].id),
            "to_customer_id": str(context["destination"].id),
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"] == (
        "Only sold product units can be transferred."
    )


def test_approve_product_transfer_rejects_second_approval(
    client,
    db,
):
    context = create_transfer_context(db)

    create_response = create_transfer(client, context)
    transfer_id = create_response.json()["transfer_id"]

    first = client.post(
        f"/product-transfers/{transfer_id}/approve",
        headers=auth_headers(context["token"]),
    )

    assert first.status_code == 200

    second = client.post(
        f"/product-transfers/{transfer_id}/approve",
        headers=auth_headers(context["token"]),
    )

    assert second.status_code == 409
    assert (
        second.json()["detail"]
        == "Only pending transfers can be approved."
    )


def test_reject_product_transfer_rejects_second_rejection(
    client,
    db,
):
    context = create_transfer_context(db)

    create_response = create_transfer(client, context)
    transfer_id = create_response.json()["transfer_id"]

    first = client.post(
        f"/product-transfers/{transfer_id}/reject",
        headers=auth_headers(context["token"]),
        json={
            "rejection_reason": "First rejection",
        },
    )

    assert first.status_code == 200

    second = client.post(
        f"/product-transfers/{transfer_id}/reject",
        headers=auth_headers(context["token"]),
        json={
            "rejection_reason": "Second rejection",
        },
    )

    assert second.status_code == 409
    assert (
        second.json()["detail"]
        == "Only pending transfers can be rejected."
    )


def test_reject_product_transfer_rejects_empty_reason(
    client,
    db,
):
    context = create_transfer_context(db)

    create_response = create_transfer(client, context)
    transfer_id = create_response.json()["transfer_id"]

    response = client.post(
        f"/product-transfers/{transfer_id}/reject",
        headers=auth_headers(context["token"]),
        json={
            "rejection_reason": "",
        },
    )

    assert response.status_code == 422


def test_create_product_transfer_rejects_inactive_source_customer(
    client,
    db,
):
    context = create_transfer_context(db)

    context["source"].status = "inactive"
    db.commit()

    response = client.post(
        "/product-transfers",
        headers=auth_headers(context["token"]),
        json={
            "product_unit_id": str(context["unit"].id),
            "from_customer_id": str(context["source"].id),
            "to_customer_id": str(context["destination"].id),
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"] == (
        "Source customer is not active."
    )


def test_create_product_transfer_rejects_inactive_destination_customer(
    client,
    db,
):
    context = create_transfer_context(db)

    context["destination"].status = "inactive"
    db.commit()

    response = client.post(
        "/product-transfers",
        headers=auth_headers(context["token"]),
        json={
            "product_unit_id": str(context["unit"].id),
            "from_customer_id": str(context["source"].id),
            "to_customer_id": str(context["destination"].id),
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"] == (
        "Destination customer is not active."
    )
