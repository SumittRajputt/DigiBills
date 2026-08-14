from decimal import Decimal
from uuid import uuid4

import pytest

from app.models.inventory_item import InventoryItem
from app.models.inventory_location import InventoryLocation
from app.models.product import Product
from app.models.product_variant import ProductVariant
from app.models.purchase_order_item import PurchaseOrderItem
from app.models.retailer import Retailer
from app.models.supplier import Supplier
from app.models.user import User
from app.services.purchase_order_service import (
    add_purchase_order_item,
    create_purchase_order,
    receive_purchase_order_item,
    update_purchase_order_status,
)


def create_purchase_context(db):
    user = User(
        phone_number=f"7{uuid4().hex[:9]}",
        status="active",
    )
    db.add(user)
    db.flush()

    retailer = Retailer(
        retailer_id=f"RET-PO-{uuid4().hex[:8].upper()}",
        owner_user_id=user.id,
        business_name="Purchase Test Retailer",
        phone_number=user.phone_number,
        status="active",
    )
    db.add(retailer)
    db.flush()

    supplier = Supplier(
        supplier_id=f"SUP-PO-{uuid4().hex[:8].upper()}",
        retailer_id=retailer.id,
        name="Purchase Test Supplier",
        phone_number=f"8{uuid4().hex[:9]}",
        is_active=True,
    )
    db.add(supplier)
    db.flush()

    location = InventoryLocation(
        retailer_id=retailer.id,
        name="Purchase Test Store",
        location_type="store",
        is_active=True,
    )
    db.add(location)
    db.flush()

    product = Product(
        product_code=f"PROD-PO-{uuid4().hex[:8].upper()}",
        name="Purchase Test Product",
        status="active",
    )
    db.add(product)
    db.flush()

    variant = ProductVariant(
        product_id=product.id,
        sku=f"SKU-PO-{uuid4().hex[:8].upper()}",
        variant_name="Purchase Test Variant",
        purchase_cost=Decimal("1000.00"),
        selling_price=Decimal("1500.00"),
        tax_rate=Decimal("18.00"),
        track_inventory=True,
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

    return (
        user,
        retailer,
        supplier,
        location,
        variant,
        inventory,
        purchase_order,
    )


def test_create_purchase_order(db):
    (
        user,
        retailer,
        supplier,
        location,
        variant,
        inventory,
        purchase_order,
    ) = create_purchase_context(db)

    assert purchase_order.status == "draft"
    assert purchase_order.retailer_id == retailer.id
    assert purchase_order.supplier_id == supplier.id
    assert purchase_order.location_id == location.id
    assert purchase_order.created_by_user_id == user.id
    assert purchase_order.subtotal == Decimal("0.00")
    assert purchase_order.tax_amount == Decimal("0.00")
    assert purchase_order.total_amount == Decimal("0.00")


def test_add_purchase_order_item_calculates_totals(db):
    (
        user,
        retailer,
        supplier,
        location,
        variant,
        inventory,
        purchase_order,
    ) = create_purchase_context(db)

    item = add_purchase_order_item(
        db=db,
        purchase_order=purchase_order,
        product_variant=variant,
        ordered_quantity=10,
        unit_cost=Decimal("1000.00"),
        tax_rate=Decimal("18.00"),
    )

    assert item.ordered_quantity == 10
    assert item.received_quantity == 0
    assert item.unit_cost == Decimal("1000.00")
    assert item.tax_amount == Decimal("1800.00")
    assert item.line_total == Decimal("11800.00")

    assert purchase_order.subtotal == Decimal("10000.00")
    assert purchase_order.tax_amount == Decimal("1800.00")
    assert purchase_order.total_amount == Decimal("11800.00")


def test_receive_purchase_order_partially_updates_inventory(db):
    (
        user,
        retailer,
        supplier,
        location,
        variant,
        inventory,
        purchase_order,
    ) = create_purchase_context(db)

    item = add_purchase_order_item(
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

    receive_purchase_order_item(
        db=db,
        purchase_order=purchase_order,
        purchase_order_item=item,
        retailer=retailer,
        location=location,
        product_variant=variant,
        inventory_item=inventory,
        received_quantity=4,
        performed_by_user_id=user.id,
    )

    assert item.received_quantity == 4
    assert purchase_order.status == "partially_received"
    assert inventory.quantity_on_hand == 4


def test_receive_remaining_quantity_completes_purchase_order(db):
    (
        user,
        retailer,
        supplier,
        location,
        variant,
        inventory,
        purchase_order,
    ) = create_purchase_context(db)

    item = add_purchase_order_item(
        db=db,
        purchase_order=purchase_order,
        product_variant=variant,
        ordered_quantity=10,
        unit_cost=Decimal("1000.00"),
    )

    update_purchase_order_status(
        db=db,
        purchase_order=purchase_order,
        status="ordered",
    )

    receive_purchase_order_item(
        db=db,
        purchase_order=purchase_order,
        purchase_order_item=item,
        retailer=retailer,
        location=location,
        product_variant=variant,
        inventory_item=inventory,
        received_quantity=10,
        performed_by_user_id=user.id,
    )

    assert item.received_quantity == 10
    assert purchase_order.status == "received"
    assert purchase_order.received_at is not None
    assert inventory.quantity_on_hand == 10


def test_receive_purchase_order_rejects_over_receiving(db):
    (
        user,
        retailer,
        supplier,
        location,
        variant,
        inventory,
        purchase_order,
    ) = create_purchase_context(db)

    item = add_purchase_order_item(
        db=db,
        purchase_order=purchase_order,
        product_variant=variant,
        ordered_quantity=5,
        unit_cost=Decimal("1000.00"),
    )

    update_purchase_order_status(
        db=db,
        purchase_order=purchase_order,
        status="ordered",
    )

    with pytest.raises(
        ValueError,
        match="cannot exceed the remaining ordered quantity",
    ):
        receive_purchase_order_item(
            db=db,
            purchase_order=purchase_order,
            purchase_order_item=item,
            retailer=retailer,
            location=location,
            product_variant=variant,
            inventory_item=inventory,
            received_quantity=6,
            performed_by_user_id=user.id,
        )

    assert item.received_quantity == 0
    assert inventory.quantity_on_hand == 0


def test_purchase_order_rejects_invalid_status(db):
    (
        user,
        retailer,
        supplier,
        location,
        variant,
        inventory,
        purchase_order,
    ) = create_purchase_context(db)

    with pytest.raises(
        ValueError,
        match="Invalid purchase order status",
    ):
        update_purchase_order_status(
            db=db,
            purchase_order=purchase_order,
            status="something_invalid",
        )


def test_purchase_order_item_cannot_be_added_after_ordered(db):
    (
        user,
        retailer,
        supplier,
        location,
        variant,
        inventory,
        purchase_order,
    ) = create_purchase_context(db)

    update_purchase_order_status(
        db=db,
        purchase_order=purchase_order,
        status="ordered",
    )

    with pytest.raises(
        ValueError,
        match="only be added to a draft",
    ):
        add_purchase_order_item(
            db=db,
            purchase_order=purchase_order,
            product_variant=variant,
            ordered_quantity=5,
            unit_cost=Decimal("1000.00"),
        )


def test_purchase_order_rejects_invalid_item_quantity(db):
    (
        user,
        retailer,
        supplier,
        location,
        variant,
        inventory,
        purchase_order,
    ) = create_purchase_context(db)

    with pytest.raises(
        ValueError,
        match="greater than zero",
    ):
        add_purchase_order_item(
            db=db,
            purchase_order=purchase_order,
            product_variant=variant,
            ordered_quantity=0,
            unit_cost=Decimal("1000.00"),
        )


def test_purchase_order_rejects_negative_unit_cost(db):
    (
        user,
        retailer,
        supplier,
        location,
        variant,
        inventory,
        purchase_order,
    ) = create_purchase_context(db)

    with pytest.raises(
        ValueError,
        match="Unit cost cannot be negative",
    ):
        add_purchase_order_item(
            db=db,
            purchase_order=purchase_order,
            product_variant=variant,
            ordered_quantity=5,
            unit_cost=Decimal("-1.00"),
        )


def test_purchase_order_rejects_negative_tax_rate(db):
    (
        user,
        retailer,
        supplier,
        location,
        variant,
        inventory,
        purchase_order,
    ) = create_purchase_context(db)

    with pytest.raises(
        ValueError,
        match="Tax rate cannot be negative",
    ):
        add_purchase_order_item(
            db=db,
            purchase_order=purchase_order,
            product_variant=variant,
            ordered_quantity=5,
            unit_cost=Decimal("1000.00"),
            tax_rate=Decimal("-1.00"),
        )


def test_purchase_order_cannot_receive_while_draft(db):
    (
        user,
        retailer,
        supplier,
        location,
        variant,
        inventory,
        purchase_order,
    ) = create_purchase_context(db)

    item = add_purchase_order_item(
        db=db,
        purchase_order=purchase_order,
        product_variant=variant,
        ordered_quantity=5,
        unit_cost=Decimal("1000.00"),
    )

    with pytest.raises(
        ValueError,
        match="not available for receiving",
    ):
        receive_purchase_order_item(
            db=db,
            purchase_order=purchase_order,
            purchase_order_item=item,
            retailer=retailer,
            location=location,
            product_variant=variant,
            inventory_item=inventory,
            received_quantity=1,
            performed_by_user_id=user.id,
        )


def test_purchase_order_rejects_invalid_received_quantity(db):
    (
        user,
        retailer,
        supplier,
        location,
        variant,
        inventory,
        purchase_order,
    ) = create_purchase_context(db)

    item = add_purchase_order_item(
        db=db,
        purchase_order=purchase_order,
        product_variant=variant,
        ordered_quantity=5,
        unit_cost=Decimal("1000.00"),
    )

    update_purchase_order_status(
        db=db,
        purchase_order=purchase_order,
        status="ordered",
    )

    with pytest.raises(
        ValueError,
        match="Received quantity must be greater than zero",
    ):
        receive_purchase_order_item(
            db=db,
            purchase_order=purchase_order,
            purchase_order_item=item,
            retailer=retailer,
            location=location,
            product_variant=variant,
            inventory_item=inventory,
            received_quantity=0,
            performed_by_user_id=user.id,
        )


def test_cancelled_purchase_order_cannot_be_reopened(db):
    (
        user,
        retailer,
        supplier,
        location,
        variant,
        inventory,
        purchase_order,
    ) = create_purchase_context(db)

    update_purchase_order_status(
        db=db,
        purchase_order=purchase_order,
        status="cancelled",
    )

    with pytest.raises(
        ValueError,
        match="cannot be reopened",
    ):
        update_purchase_order_status(
            db=db,
            purchase_order=purchase_order,
            status="ordered",
        )
