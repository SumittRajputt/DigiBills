from decimal import Decimal
import uuid

import pytest

from app.models.customer import Customer
from app.models.invoice import Invoice
from app.models.invoice_item import InvoiceItem
from app.models.product import Product
from app.models.product_ownership import ProductOwnership
from app.models.product_variant import ProductVariant
from app.models.retailer import Retailer
from app.models.product_unit import ProductUnit
from app.models.user import User
from app.services.product_ownership_service import assign_product_ownership
from app.services.product_transfer_service import (
    create_product_transfer,
    approve_product_transfer,
    reject_product_transfer,
)


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


def create_serialized_product_unit(db):
    product = Product(
        product_code=f"PROD-{uuid.uuid4().hex[:8].upper()}",
        name="Transfer Test Product",
        status="active",
    )
    db.add(product)
    db.flush()

    variant = ProductVariant(
        product_id=product.id,
        sku=f"SKU-{uuid.uuid4().hex[:8].upper()}",
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

    unit = ProductUnit(
        product_variant_id=variant.id,
        serial_number=f"SN-{uuid.uuid4().hex[:12].upper()}",
        status="in_stock",
    )
    db.add(unit)
    db.flush()

    return variant, unit


def create_invoice_context(db, customer, variant):
    retailer_user = User(
        phone_number=f"8{uuid.uuid4().hex[:9]}",
        status="active",
    )
    db.add(retailer_user)
    db.flush()

    retailer = Retailer(
        retailer_id=f"RET-{uuid.uuid4().hex[:8].upper()}",
        owner_user_id=retailer_user.id,
        business_name="Transfer Test Retailer",
        phone_number=retailer_user.phone_number,
        status="active",
    )
    db.add(retailer)
    db.flush()

    invoice = Invoice(
        invoice_id=f"INV-{uuid.uuid4().hex[:10].upper()}",
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
        product_name="Transfer Test Product",
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

    return invoice, invoice_item


def test_assign_product_ownership(db):
    customer = create_customer(db, "Original Owner")
    variant, unit = create_serialized_product_unit(db)

    invoice, invoice_item = create_invoice_context(
        db,
        customer,
        variant,
    )

    ownership = assign_product_ownership(
        db=db,
        invoice=invoice,
        invoice_item=invoice_item,
        customer=customer,
        product_unit=unit,
    )

    db.flush()

    assert ownership.customer_id == customer.id
    assert ownership.product_unit_id == unit.id
    assert ownership.ownership_status == "active"
    assert unit.status == "sold"


def test_transfer_can_be_created(db):
    source = create_customer(db, "Source Customer")
    destination = create_customer(db, "Destination Customer")

    variant, unit = create_serialized_product_unit(db)

    invoice, invoice_item = create_invoice_context(
        db,
        source,
        variant,
    )

    assign_product_ownership(
        db=db,
        invoice=invoice,
        invoice_item=invoice_item,
        customer=source,
        product_unit=unit,
    )

    db.flush()

    transfer = create_product_transfer(
        db=db,
        product_unit=unit,
        from_customer=source,
        to_customer=destination,
        requested_by_user_id=source.user_id,
        reason="Customer ownership transfer",
    )

    assert transfer.status == "pending"
    assert transfer.product_unit_id == unit.id
    assert transfer.from_customer_id == source.id
    assert transfer.to_customer_id == destination.id


def test_transfer_approval_changes_ownership(db):
    source = create_customer(db, "Source Customer")
    destination = create_customer(db, "Destination Customer")

    variant, unit = create_serialized_product_unit(db)

    invoice, invoice_item = create_invoice_context(
        db,
        source,
        variant,
    )

    assign_product_ownership(
        db=db,
        invoice=invoice,
        invoice_item=invoice_item,
        customer=source,
        product_unit=unit,
    )

    db.flush()

    transfer = create_product_transfer(
        db=db,
        product_unit=unit,
        from_customer=source,
        to_customer=destination,
        requested_by_user_id=source.user_id,
    )

    transfer = approve_product_transfer(
        db=db,
        transfer=transfer,
        approved_by_user_id=source.user_id,
    )

    ownerships = (
        db.query(ProductOwnership)
        .filter(
            ProductOwnership.product_unit_id == unit.id,
        )
        .all()
    )

    active_ownerships = [
        ownership
        for ownership in ownerships
        if ownership.ownership_status == "active"
    ]

    released_ownerships = [
        ownership
        for ownership in ownerships
        if ownership.ownership_status == "released"
    ]

    assert transfer.status == "completed"
    assert len(active_ownerships) == 1
    assert active_ownerships[0].customer_id == destination.id
    assert len(released_ownerships) == 1
    assert released_ownerships[0].customer_id == source.id


def test_transfer_rejection_does_not_change_ownership(db):
    source = create_customer(db, "Source Customer")
    destination = create_customer(db, "Destination Customer")

    variant, unit = create_serialized_product_unit(db)

    invoice, invoice_item = create_invoice_context(
        db,
        source,
        variant,
    )

    assign_product_ownership(
        db=db,
        invoice=invoice,
        invoice_item=invoice_item,
        customer=source,
        product_unit=unit,
    )

    db.flush()

    transfer = create_product_transfer(
        db=db,
        product_unit=unit,
        from_customer=source,
        to_customer=destination,
        requested_by_user_id=source.user_id,
    )

    transfer = reject_product_transfer(
        db=db,
        transfer=transfer,
        rejected_by_user_id=uuid.uuid4(),
        rejection_reason="Transfer not authorized",
    )

    ownership = (
        db.query(ProductOwnership)
        .filter(
            ProductOwnership.product_unit_id == unit.id,
            ProductOwnership.ownership_status == "active",
        )
        .one()
    )

    assert transfer.status == "rejected"
    assert ownership.customer_id == source.id
    assert unit.status == "sold"


def test_transfer_rejects_same_customer(db):
    customer = create_customer(db, "Same Customer")
    variant, unit = create_serialized_product_unit(db)

    invoice, invoice_item = create_invoice_context(
        db,
        customer,
        variant,
    )

    assign_product_ownership(
        db=db,
        invoice=invoice,
        invoice_item=invoice_item,
        customer=customer,
        product_unit=unit,
    )

    db.flush()

    with pytest.raises(
        ValueError,
        match="different",
    ):
        create_product_transfer(
            db=db,
            product_unit=unit,
            from_customer=customer,
            to_customer=customer,
            requested_by_user_id=uuid.uuid4(),
        )
