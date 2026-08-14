from decimal import Decimal
from uuid import uuid4

import pytest

from app.models.inventory_item import InventoryItem
from app.models.inventory_location import InventoryLocation
from app.models.product import Product
from app.models.product_variant import ProductVariant
from app.models.purchase_return_item import PurchaseReturnItem
from app.models.retailer import Retailer
from app.models.supplier import Supplier
from app.models.user import User
from app.services.purchase_order_service import (
    add_purchase_order_item,
    create_purchase_order,
    receive_purchase_order_item,
    update_purchase_order_status,
)
from app.services.purchase_return_service import (
    add_purchase_return_item,
    create_purchase_return,
    process_purchase_return,
)


def create_purchase_return_context(db, ordered_quantity=10):
    user = User(
        phone_number=f"7{uuid4().hex[:9]}",
        status="active",
    )
    db.add(user)
    db.flush()

    retailer = Retailer(
        retailer_id=f"RET-PR-{uuid4().hex[:8].upper()}",
        owner_user_id=user.id,
        business_name="Purchase Return Test Retailer",
        phone_number=user.phone_number,
        status="active",
    )
    db.add(retailer)
    db.flush()

    supplier = Supplier(
        supplier_id=f"SUP-PR-{uuid4().hex[:8].upper()}",
        retailer_id=retailer.id,
        name="Purchase Return Test Supplier",
        phone_number=f"8{uuid4().hex[:9]}",
        is_active=True,
    )
    db.add(supplier)
    db.flush()

    location = InventoryLocation(
        retailer_id=retailer.id,
        name="Purchase Return Test Store",
        location_type="store",
        is_active=True,
    )
    db.add(location)
    db.flush()

    product = Product(
        product_code=f"PROD-PR-{uuid4().hex[:8].upper()}",
        name="Purchase Return Test Product",
        status="active",
    )
    db.add(product)
    db.flush()

    variant = ProductVariant(
        product_id=product.id,
        sku=f"SKU-PR-{uuid4().hex[:8].upper()}",
        variant_name="Purchase Return Test Variant",
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

    purchase_order_item = add_purchase_order_item(
        db=db,
        purchase_order=purchase_order,
        product_variant=variant,
        ordered_quantity=ordered_quantity,
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
        purchase_order_item=purchase_order_item,
        retailer=retailer,
        location=location,
        product_variant=variant,
        inventory_item=inventory,
        received_quantity=ordered_quantity,
        performed_by_user_id=user.id,
    )

    purchase_return = create_purchase_return(
        db=db,
        retailer=retailer,
        purchase_order=purchase_order,
        supplier=supplier,
        location=location,
        reason="Damaged stock",
        notes="Return to supplier",
    )

    return (
        user,
        retailer,
        supplier,
        location,
        variant,
        inventory,
        purchase_order,
        purchase_order_item,
        purchase_return,
    )


def test_create_purchase_return(db):
    (
        user,
        retailer,
        supplier,
        location,
        variant,
        inventory,
        purchase_order,
        purchase_order_item,
        purchase_return,
    ) = create_purchase_return_context(db)

    assert purchase_return.status == "requested"
    assert purchase_return.retailer_id == retailer.id
    assert purchase_return.supplier_id == supplier.id
    assert purchase_return.location_id == location.id
    assert purchase_return.purchase_order_id == purchase_order.id
    assert purchase_return.return_amount == Decimal("0.00")
    assert purchase_return.reason == "Damaged stock"


def test_add_purchase_return_item_calculates_amount(db):
    (
        user,
        retailer,
        supplier,
        location,
        variant,
        inventory,
        purchase_order,
        purchase_order_item,
        purchase_return,
    ) = create_purchase_return_context(db)

    item = add_purchase_return_item(
        db=db,
        purchase_return=purchase_return,
        purchase_order_item=purchase_order_item,
        product_variant=variant,
        quantity=3,
        reason="Three damaged units",
        condition="damaged",
    )

    assert item.quantity == 3
    assert item.unit_cost == Decimal("1000.00")
    assert item.return_amount == Decimal("3000.00")
    assert item.condition == "damaged"
    assert purchase_return.return_amount == Decimal("3000.00")


def test_add_purchase_return_item_can_accumulate_quantity(db):
    (
        user,
        retailer,
        supplier,
        location,
        variant,
        inventory,
        purchase_order,
        purchase_order_item,
        purchase_return,
    ) = create_purchase_return_context(db)

    first_item = add_purchase_return_item(
        db=db,
        purchase_return=purchase_return,
        purchase_order_item=purchase_order_item,
        product_variant=variant,
        quantity=2,
    )

    second_item = add_purchase_return_item(
        db=db,
        purchase_return=purchase_return,
        purchase_order_item=purchase_order_item,
        product_variant=variant,
        quantity=3,
    )

    assert first_item.id == second_item.id
    assert second_item.quantity == 5
    assert second_item.return_amount == Decimal("5000.00")
    assert purchase_return.return_amount == Decimal("5000.00")


def test_process_purchase_return_reduces_inventory(db):
    (
        user,
        retailer,
        supplier,
        location,
        variant,
        inventory,
        purchase_order,
        purchase_order_item,
        purchase_return,
    ) = create_purchase_return_context(db)

    add_purchase_return_item(
        db=db,
        purchase_return=purchase_return,
        purchase_order_item=purchase_order_item,
        product_variant=variant,
        quantity=4,
    )

    process_purchase_return(
        db=db,
        purchase_return=purchase_return,
        retailer=retailer,
        processed_by_user_id=user.id,
    )

    assert purchase_return.status == "processed"
    assert purchase_return.processed_by_user_id == user.id
    assert purchase_return.processed_at is not None
    assert inventory.quantity_on_hand == 6


def test_create_purchase_return_rejects_draft_purchase_order(db):
    (
        user,
        retailer,
        supplier,
        location,
        variant,
        inventory,
        purchase_order,
        purchase_order_item,
        purchase_return,
    ) = create_purchase_return_context(db)

    purchase_return.status = "requested"

    purchase_order.status = "draft"
    db.flush()

    with pytest.raises(
        ValueError,
        match="no received stock available for return",
    ):
        create_purchase_return(
            db=db,
            retailer=retailer,
            purchase_order=purchase_order,
            supplier=supplier,
            location=location,
        )


def test_purchase_return_rejects_quantity_above_received(db):
    (
        user,
        retailer,
        supplier,
        location,
        variant,
        inventory,
        purchase_order,
        purchase_order_item,
        purchase_return,
    ) = create_purchase_return_context(db)

    with pytest.raises(
        ValueError,
        match="cannot exceed received quantity",
    ):
        add_purchase_return_item(
            db=db,
            purchase_return=purchase_return,
            purchase_order_item=purchase_order_item,
            product_variant=variant,
            quantity=11,
        )


def test_purchase_return_rejects_invalid_condition(db):
    (
        user,
        retailer,
        supplier,
        location,
        variant,
        inventory,
        purchase_order,
        purchase_order_item,
        purchase_return,
    ) = create_purchase_return_context(db)

    with pytest.raises(
        ValueError,
        match="Invalid return condition",
    ):
        add_purchase_return_item(
            db=db,
            purchase_return=purchase_return,
            purchase_order_item=purchase_order_item,
            product_variant=variant,
            quantity=1,
            condition="unknown",
        )


def test_purchase_return_rejects_zero_quantity(db):
    (
        user,
        retailer,
        supplier,
        location,
        variant,
        inventory,
        purchase_order,
        purchase_order_item,
        purchase_return,
    ) = create_purchase_return_context(db)

    with pytest.raises(
        ValueError,
        match="Return quantity must be greater than zero",
    ):
        add_purchase_return_item(
            db=db,
            purchase_return=purchase_return,
            purchase_order_item=purchase_order_item,
            product_variant=variant,
            quantity=0,
        )


def test_purchase_return_rejects_processing_without_items(db):
    (
        user,
        retailer,
        supplier,
        location,
        variant,
        inventory,
        purchase_order,
        purchase_order_item,
        purchase_return,
    ) = create_purchase_return_context(db)

    with pytest.raises(
        ValueError,
        match="must contain at least one item",
    ):
        process_purchase_return(
            db=db,
            purchase_return=purchase_return,
            retailer=retailer,
            processed_by_user_id=user.id,
        )


def test_purchase_return_rejects_insufficient_inventory(db):
    (
        user,
        retailer,
        supplier,
        location,
        variant,
        inventory,
        purchase_order,
        purchase_order_item,
        purchase_return,
    ) = create_purchase_return_context(db)

    add_purchase_return_item(
        db=db,
        purchase_return=purchase_return,
        purchase_order_item=purchase_order_item,
        product_variant=variant,
        quantity=4,
    )

    inventory.quantity_on_hand = 2
    db.commit()

    with pytest.raises(
        ValueError,
        match="Insufficient available stock",
    ):
        process_purchase_return(
            db=db,
            purchase_return=purchase_return,
            retailer=retailer,
            processed_by_user_id=user.id,
        )

    assert purchase_return.status == "requested"
    assert inventory.quantity_on_hand == 2


def test_purchase_return_cannot_be_processed_twice(db):
    (
        user,
        retailer,
        supplier,
        location,
        variant,
        inventory,
        purchase_order,
        purchase_order_item,
        purchase_return,
    ) = create_purchase_return_context(db)

    add_purchase_return_item(
        db=db,
        purchase_return=purchase_return,
        purchase_order_item=purchase_order_item,
        product_variant=variant,
        quantity=2,
    )

    process_purchase_return(
        db=db,
        purchase_return=purchase_return,
        retailer=retailer,
        processed_by_user_id=user.id,
    )

    with pytest.raises(
        ValueError,
        match="Only requested purchase returns can be processed",
    ):
        process_purchase_return(
            db=db,
            purchase_return=purchase_return,
            retailer=retailer,
            processed_by_user_id=user.id,
        )

    assert inventory.quantity_on_hand == 8
