from decimal import Decimal
import uuid

import pytest

from app.models.product import Product
from app.models.product_variant import ProductVariant
from app.models.product_unit import ProductUnit
from app.services.product_unit_service import create_product_unit


def create_serialized_variant(db):
    product = Product(
        product_code=f"PROD-UNIT-{uuid.uuid4().hex[:8].upper()}",
        name="Test Serialized Product",
        status="active",
    )
    db.add(product)
    db.flush()

    variant = ProductVariant(
        product_id=product.id,
        sku=f"UNIT-SKU-{uuid.uuid4().hex[:8].upper()}",
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

    return variant


def test_create_product_unit(db):
    variant = create_serialized_variant(db)

    unit = create_product_unit(
        db=db,
        product_variant_id=str(variant.id),
        serial_number=f"SN-{uuid.uuid4().hex[:12].upper()}",
    )

    assert unit.id is not None
    assert unit.product_variant_id == variant.id
    assert unit.status == "in_stock"


def test_duplicate_serial_number_is_rejected(db):
    variant = create_serialized_variant(db)

    serial_number = f"SN-{uuid.uuid4().hex[:12].upper()}"

    create_product_unit(
        db=db,
        product_variant_id=str(variant.id),
        serial_number=serial_number,
    )

    with pytest.raises(
        ValueError,
        match="already exists",
    ):
        create_product_unit(
            db=db,
            product_variant_id=str(variant.id),
            serial_number=serial_number,
        )


def test_product_unit_requires_serialized_variant(db):
    product = Product(
        product_code=f"PROD-NONSERIAL-{uuid.uuid4().hex[:8].upper()}",
        name="Test Non Serialized Product",
        status="active",
    )
    db.add(product)
    db.flush()

    variant = ProductVariant(
        product_id=product.id,
        sku=f"NON-SERIAL-{uuid.uuid4().hex[:8].upper()}",
        variant_name="Non Serialized Variant",
        purchase_cost=Decimal("100.00"),
        selling_price=Decimal("150.00"),
        tax_rate=Decimal("18.00"),
        track_inventory=True,
        requires_serial_number=False,
        status="active",
    )
    db.add(variant)
    db.flush()

    with pytest.raises(
        ValueError,
        match="does not require serial number tracking",
    ):
        create_product_unit(
            db=db,
            product_variant_id=str(variant.id),
            serial_number=f"SN-{uuid.uuid4().hex[:12].upper()}",
        )


def test_serialized_invoice_sells_selected_units_and_creates_ownership(db):
    from app.models.customer import Customer
    from app.models.inventory_item import InventoryItem
    from app.models.inventory_location import InventoryLocation
    from app.models.invoice_item_unit import InvoiceItemUnit
    from app.models.product_ownership import ProductOwnership
    from app.models.retailer import Retailer
    from app.models.user import User
    from app.services.invoice_service import create_invoice

    user = User(
        phone_number=f"999{uuid.uuid4().hex[:7]}",
        email=f"serialized-{uuid.uuid4().hex[:8]}@example.com",
        status="active",
    )
    db.add(user)
    db.flush()

    retailer = Retailer(
        retailer_id=f"RET-{uuid.uuid4().hex[:8].upper()}",
        owner_user_id=user.id,
        business_name="Serialized Test Retailer",
        phone_number=user.phone_number,
        status="active",
    )
    db.add(retailer)
    db.flush()

    location = InventoryLocation(
        retailer_id=retailer.id,
        name="Serialized Test Store",
        location_type="store",
        is_active=True,
    )
    db.add(location)
    db.flush()

    customer_user = User(
        phone_number=f"888{uuid.uuid4().hex[:7]}",
        status="active",
    )
    db.add(customer_user)
    db.flush()

    customer = Customer(
        customer_id=f"CUS-{uuid.uuid4().hex[:8].upper()}",
        user_id=customer_user.id,
        full_name="Serialized Test Customer",
        phone_number=customer_user.phone_number,
        status="active",
    )
    db.add(customer)
    db.flush()

    variant = create_serialized_variant(db)

    inventory = InventoryItem(
        retailer_id=retailer.id,
        location_id=location.id,
        product_variant_id=variant.id,
        quantity_on_hand=2,
        quantity_reserved=0,
        average_cost=Decimal("10000.00"),
    )
    db.add(inventory)
    db.flush()

    unit_1 = create_product_unit(
        db=db,
        product_variant_id=str(variant.id),
        serial_number=f"SN-{uuid.uuid4().hex[:12].upper()}",
    )

    unit_2 = create_product_unit(
        db=db,
        product_variant_id=str(variant.id),
        serial_number=f"SN-{uuid.uuid4().hex[:12].upper()}",
    )

    class InvoiceItem:
        sku = variant.sku
        quantity = 2
        product_unit_ids = [
            str(unit_1.id),
            str(unit_2.id),
        ]
        unit_price = Decimal("15000.00")
        discount_amount = Decimal("0.00")

    invoice = create_invoice(
        db=db,
        retailer=retailer,
        customer=customer,
        location=location,
        items=[InvoiceItem()],
        invoice_number=f"SERIAL-{uuid.uuid4().hex[:8].upper()}",
        invoice_discount=Decimal("0.00"),
        user_id=user.id,
    )

    db.refresh(unit_1)
    db.refresh(unit_2)

    assert invoice.status == "active"
    assert inventory.quantity_on_hand == 0
    assert unit_1.status == "sold"
    assert unit_2.status == "sold"

    mappings = (
        db.query(InvoiceItemUnit)
        .filter(
            InvoiceItemUnit.invoice_item_id == invoice.items[0].id
        )
        .all()
    )

    assert len(mappings) == 2

    ownerships = (
        db.query(ProductOwnership)
        .filter(
            ProductOwnership.customer_id == customer.id,
            ProductOwnership.ownership_status == "active",
        )
        .all()
    )

    assert len(ownerships) == 2
    assert {
        ownership.product_unit_id
        for ownership in ownerships
    } == {unit_1.id, unit_2.id}


def test_serialized_invoice_rejects_already_sold_unit(db):
    from app.models.customer import Customer
    from app.models.inventory_item import InventoryItem
    from app.models.inventory_location import InventoryLocation
    from app.models.retailer import Retailer
    from app.models.user import User
    from app.services.invoice_service import create_invoice

    user = User(
        phone_number=f"999{uuid.uuid4().hex[:7]}",
        email=f"serialized-reuse-{uuid.uuid4().hex[:8]}@example.com",
        status="active",
    )
    db.add(user)
    db.flush()

    retailer = Retailer(
        retailer_id=f"RET-{uuid.uuid4().hex[:8].upper()}",
        owner_user_id=user.id,
        business_name="Serialized Reuse Retailer",
        phone_number=user.phone_number,
        status="active",
    )
    db.add(retailer)
    db.flush()

    location = InventoryLocation(
        retailer_id=retailer.id,
        name="Reuse Test Store",
        location_type="store",
        is_active=True,
    )
    db.add(location)
    db.flush()

    customer_user = User(
        phone_number=f"888{uuid.uuid4().hex[:7]}",
        status="active",
    )
    db.add(customer_user)
    db.flush()

    customer = Customer(
        customer_id=f"CUS-{uuid.uuid4().hex[:8].upper()}",
        user_id=customer_user.id,
        full_name="Reuse Test Customer",
        phone_number=customer_user.phone_number,
        status="active",
    )
    db.add(customer)
    db.flush()

    variant = create_serialized_variant(db)

    inventory = InventoryItem(
        retailer_id=retailer.id,
        location_id=location.id,
        product_variant_id=variant.id,
        quantity_on_hand=2,
        quantity_reserved=0,
        average_cost=Decimal("10000.00"),
    )
    db.add(inventory)
    db.flush()

    unit = create_product_unit(
        db=db,
        product_variant_id=str(variant.id),
        serial_number=f"SN-{uuid.uuid4().hex[:12].upper()}",
    )

    class InvoiceItem:
        sku = variant.sku
        quantity = 1
        product_unit_ids = [str(unit.id)]
        unit_price = Decimal("15000.00")
        discount_amount = Decimal("0.00")

    create_invoice(
        db=db,
        retailer=retailer,
        customer=customer,
        location=location,
        items=[InvoiceItem()],
        invoice_number=f"SERIAL-{uuid.uuid4().hex[:8].upper()}",
        user_id=user.id,
    )

    with pytest.raises(
        ValueError,
        match="not available for sale",
    ):
        create_invoice(
            db=db,
            retailer=retailer,
            customer=customer,
            location=location,
            items=[InvoiceItem()],
            invoice_number=f"SERIAL-{uuid.uuid4().hex[:8].upper()}",
            user_id=user.id,
        )


def test_serialized_sales_return_releases_unit_and_restores_inventory(db):
    from app.models.customer import Customer
    from app.models.inventory_item import InventoryItem
    from app.models.inventory_location import InventoryLocation
    from app.models.product_ownership import ProductOwnership
    from app.models.retailer import Retailer
    from app.models.sales_return_item_unit import SalesReturnItemUnit
    from app.models.user import User
    from app.services.invoice_service import create_invoice
    from app.services.sales_return_service import (
        add_sales_return_item,
        create_sales_return,
        process_sales_return,
    )

    user = User(
        phone_number=f"999{uuid.uuid4().hex[:7]}",
        email=f"return-{uuid.uuid4().hex[:8]}@example.com",
        status="active",
    )
    db.add(user)
    db.flush()

    retailer = Retailer(
        retailer_id=f"RET-{uuid.uuid4().hex[:8].upper()}",
        owner_user_id=user.id,
        business_name="Serialized Return Retailer",
        phone_number=user.phone_number,
        status="active",
    )
    db.add(retailer)
    db.flush()

    location = InventoryLocation(
        retailer_id=retailer.id,
        name="Return Test Store",
        location_type="store",
        is_active=True,
    )
    db.add(location)
    db.flush()

    customer_user = User(
        phone_number=f"888{uuid.uuid4().hex[:7]}",
        status="active",
    )
    db.add(customer_user)
    db.flush()

    customer = Customer(
        customer_id=f"CUS-{uuid.uuid4().hex[:8].upper()}",
        user_id=customer_user.id,
        full_name="Serialized Return Customer",
        phone_number=customer_user.phone_number,
        status="active",
    )
    db.add(customer)
    db.flush()

    variant = create_serialized_variant(db)

    inventory = InventoryItem(
        retailer_id=retailer.id,
        location_id=location.id,
        product_variant_id=variant.id,
        quantity_on_hand=2,
        quantity_reserved=0,
        average_cost=Decimal("10000.00"),
    )
    db.add(inventory)
    db.flush()

    unit_1 = create_product_unit(
        db=db,
        product_variant_id=str(variant.id),
        serial_number=f"SN-{uuid.uuid4().hex[:12].upper()}",
    )

    unit_2 = create_product_unit(
        db=db,
        product_variant_id=str(variant.id),
        serial_number=f"SN-{uuid.uuid4().hex[:12].upper()}",
    )

    class InvoiceItem:
        sku = variant.sku
        quantity = 2
        product_unit_ids = [
            str(unit_1.id),
            str(unit_2.id),
        ]
        unit_price = Decimal("15000.00")
        discount_amount = Decimal("0.00")

    invoice = create_invoice(
        db=db,
        retailer=retailer,
        customer=customer,
        location=location,
        items=[InvoiceItem()],
        invoice_number=f"RETURN-{uuid.uuid4().hex[:8].upper()}",
        invoice_discount=Decimal("0.00"),
        user_id=user.id,
    )

    db.refresh(unit_1)
    db.refresh(unit_2)

    assert unit_1.status == "sold"
    assert unit_2.status == "sold"
    assert inventory.quantity_on_hand == 0

    sales_return = create_sales_return(
        db=db,
        retailer=retailer,
        invoice=invoice,
        reason="Customer return",
    )

    return_item = add_sales_return_item(
        db=db,
        sales_return=sales_return,
        invoice_item_id=str(invoice.items[0].id),
        quantity=1,
        condition="good",
        return_to_inventory=True,
        restocking_fee=Decimal("0.00"),
        product_unit_ids=[str(unit_1.id)],
    )

    mappings = (
        db.query(SalesReturnItemUnit)
        .filter(
            SalesReturnItemUnit.sales_return_item_id
            == return_item.id
        )
        .all()
    )

    assert len(mappings) == 1
    assert mappings[0].product_unit_id == unit_1.id

    processed_return = process_sales_return(
        db=db,
        sales_return=sales_return,
        retailer=retailer,
        processed_by_user_id=user.id,
        refund_method="cash",
    )

    db.refresh(unit_1)
    db.refresh(unit_2)
    db.refresh(inventory)

    assert processed_return.status == "processed"
    assert unit_1.status == "in_stock"
    assert unit_2.status == "sold"
    assert inventory.quantity_on_hand == 1

    ownership = (
        db.query(ProductOwnership)
        .filter(
            ProductOwnership.product_unit_id == unit_1.id,
            ProductOwnership.customer_id == customer.id,
        )
        .one()
    )

    assert ownership.ownership_status == "released"
