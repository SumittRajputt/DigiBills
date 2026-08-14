from decimal import Decimal
from uuid import uuid4

from app.models.customer import Customer
from app.models.invoice import Invoice
from app.models.invoice_item import InvoiceItem
from app.models.product import Product
from app.models.product_unit import ProductUnit
from app.models.product_variant import ProductVariant
from app.models.retailer import Retailer
from app.models.role import Role
from app.models.user import User
from app.models.access_control import user_roles
from app.services.auth_service import create_user_token


def create_ownership_api_context(db):
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

    customer_user = User(
        phone_number=f"888{uuid4().hex[:7]}",
        status="active",
    )
    db.add(customer_user)
    db.flush()

    customer = Customer(
        customer_id=f"CUS-{uuid4().hex[:8].upper()}",
        user_id=customer_user.id,
        full_name="Ownership API Customer",
        phone_number=customer_user.phone_number,
        status="active",
    )
    db.add(customer)
    db.flush()

    product = Product(
        product_code=f"PROD-OWN-{uuid4().hex[:8].upper()}",
        name="Ownership API Product",
        status="active",
    )
    db.add(product)
    db.flush()

    variant = ProductVariant(
        product_id=product.id,
        sku=f"OWN-API-{uuid4().hex[:8].upper()}",
        variant_name="Serialized Variant",
        purchase_cost=Decimal("10000.00"),
        selling_price=Decimal("15000.00"),
        tax_rate=Decimal("18.00"),
        track_inventory=True,
        requires_serial_number=True,
        status="active",
    )
    db.add(variant)
    db.flush()

    retailer = Retailer(
        retailer_id=f"RET-OWN-{uuid4().hex[:8].upper()}",
        owner_user_id=user.id,
        business_name="Ownership API Retailer",
        phone_number=user.phone_number,
        status="active",
    )
    db.add(retailer)
    db.flush()

    invoice = Invoice(
        invoice_id=f"INV-OWN-{uuid4().hex[:10].upper()}",
        retailer_id=retailer.id,
        customer_id=customer.id,
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

    unit = ProductUnit(
        product_variant_id=variant.id,
        serial_number=f"SN-OWN-{uuid4().hex[:12].upper()}",
        status="in_stock",
    )
    db.add(unit)
    db.commit()

    return (
        user,
        customer,
        invoice,
        invoice_item,
        unit,
    )


def test_create_product_ownership_api(client, db):
    (
        user,
        customer,
        invoice,
        invoice_item,
        unit,
    ) = create_ownership_api_context(db)

    token = create_user_token(user)

    response = client.post(
        "/product-ownerships",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "invoice_id": invoice.invoice_id,
            "invoice_item_id": str(invoice_item.id),
            "product_unit_id": str(unit.id),
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["product_unit_id"] == str(unit.id)
    assert data["customer_id"] == str(customer.id)
    assert data["ownership_status"] == "active"
    assert data["source"] == "invoice"


def test_get_product_ownership_by_serial_api(client, db):
    (
        user,
        customer,
        invoice,
        invoice_item,
        unit,
    ) = create_ownership_api_context(db)

    token = create_user_token(user)

    create_response = client.post(
        "/product-ownerships",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "invoice_id": invoice.invoice_id,
            "invoice_item_id": str(invoice_item.id),
            "product_unit_id": str(unit.id),
        },
    )

    assert create_response.status_code == 201

    response = client.get(
        f"/product-ownerships/serial/{unit.serial_number}",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["product_unit_id"] == str(unit.id)
    assert data["customer_id"] == str(customer.id)
    assert data["ownership_status"] == "active"


def test_create_product_ownership_api_rejects_wrong_variant(
    client,
    db,
):
    (
        user,
        customer,
        invoice,
        invoice_item,
        unit,
    ) = create_ownership_api_context(db)

    other_product = Product(
        product_code=f"PROD-OTHER-{uuid4().hex[:8].upper()}",
        name="Other Product",
        status="active",
    )
    db.add(other_product)
    db.flush()

    other_variant = ProductVariant(
        product_id=other_product.id,
        sku=f"OTHER-{uuid4().hex[:8].upper()}",
        variant_name="Other Serialized Variant",
        purchase_cost=Decimal("10000.00"),
        selling_price=Decimal("15000.00"),
        tax_rate=Decimal("18.00"),
        track_inventory=True,
        requires_serial_number=True,
        status="active",
    )
    db.add(other_variant)
    db.flush()

    wrong_unit = ProductUnit(
        product_variant_id=other_variant.id,
        serial_number=f"SN-WRONG-{uuid4().hex[:12].upper()}",
        status="in_stock",
    )
    db.add(wrong_unit)
    db.commit()

    token = create_user_token(user)

    response = client.post(
        "/product-ownerships",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "invoice_id": invoice.invoice_id,
            "invoice_item_id": str(invoice_item.id),
            "product_unit_id": str(wrong_unit.id),
        },
    )

    assert response.status_code == 409
    assert (
        "does not belong to the product variant"
        in response.json()["detail"]
    )
