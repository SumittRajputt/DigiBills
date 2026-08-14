import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.customer import Customer
from app.models.ownership_history import OwnershipHistory
from app.models.product_ownership import ProductOwnership
from app.models.product_transfer import ProductTransfer
from app.models.product_unit import ProductUnit


def get_product_transfer_by_id(
    db: Session,
    transfer_id: str,
) -> Optional[ProductTransfer]:
    statement = select(ProductTransfer).where(
        ProductTransfer.transfer_id == transfer_id
    )

    return db.execute(statement).scalar_one_or_none()


def get_product_unit_by_id(
    db: Session,
    product_unit_id: str,
) -> Optional[ProductUnit]:
    try:
        parsed_id = uuid.UUID(product_unit_id)
    except ValueError:
        return None

    statement = select(ProductUnit).where(
        ProductUnit.id == parsed_id
    )

    return db.execute(statement).scalar_one_or_none()


def get_customer_by_id(
    db: Session,
    customer_id: str,
) -> Optional[Customer]:
    try:
        parsed_id = uuid.UUID(customer_id)
    except ValueError:
        return None

    statement = select(Customer).where(
        Customer.id == parsed_id
    )

    return db.execute(statement).scalar_one_or_none()


def create_product_transfer(
    db: Session,
    product_unit: ProductUnit,
    from_customer: Customer,
    to_customer: Customer,
    requested_by_user_id: uuid.UUID,
    reason: Optional[str] = None,
) -> ProductTransfer:

    if from_customer.id == to_customer.id:
        raise ValueError(
            "Source and destination customers must be different."
        )

    if from_customer.status != "active":
        raise ValueError(
            "Source customer is not active."
        )

    if to_customer.status != "active":
        raise ValueError(
            "Destination customer is not active."
        )

    if product_unit.status != "sold":
        raise ValueError(
            "Only sold product units can be transferred."
        )

    ownership = db.execute(
        select(ProductOwnership).where(
            ProductOwnership.product_unit_id == product_unit.id,
            ProductOwnership.customer_id == from_customer.id,
            ProductOwnership.ownership_status == "active",
        )
    ).scalar_one_or_none()

    if ownership is None:
        raise ValueError(
            "Source customer does not currently own this product unit."
        )

    pending_transfer = db.execute(
        select(ProductTransfer).where(
            ProductTransfer.product_unit_id == product_unit.id,
            ProductTransfer.status == "pending",
        )
    ).scalar_one_or_none()

    if pending_transfer is not None:
        raise ValueError(
            "This product unit already has a pending transfer."
        )

    transfer = ProductTransfer(
        transfer_id=f"TRF-{uuid.uuid4().hex[:10].upper()}",
        product_unit_id=product_unit.id,
        from_customer_id=from_customer.id,
        to_customer_id=to_customer.id,
        requested_by_user_id=requested_by_user_id,
        approved_by_user_id=None,
        status="pending",
        reason=reason,
        rejection_reason=None,
        requested_at=datetime.now(timezone.utc),
        approved_at=None,
        completed_at=None,
    )

    db.add(transfer)
    db.commit()
    db.refresh(transfer)

    return transfer


def approve_product_transfer(
    db: Session,
    transfer: ProductTransfer,
    approved_by_user_id: uuid.UUID,
) -> ProductTransfer:

    if transfer.status != "pending":
        raise ValueError(
            "Only pending transfers can be approved."
        )

    product_unit = db.execute(
        select(ProductUnit).where(
            ProductUnit.id == transfer.product_unit_id
        )
    ).scalar_one_or_none()

    if product_unit is None:
        raise ValueError(
            "Product unit not found."
        )

    ownership = db.execute(
        select(ProductOwnership).where(
            ProductOwnership.product_unit_id == product_unit.id,
            ProductOwnership.customer_id == transfer.from_customer_id,
            ProductOwnership.ownership_status == "active",
        )
    ).scalar_one_or_none()

    if ownership is None:
        raise ValueError(
            "Source customer no longer owns this product unit."
        )

    destination_ownership = db.execute(
        select(ProductOwnership).where(
            ProductOwnership.product_unit_id == product_unit.id,
            ProductOwnership.ownership_status == "active",
        )
    ).scalar_one_or_none()

    if destination_ownership is not None:
        destination_ownership.ownership_status = "released"
        destination_ownership.released_at = datetime.now(
            timezone.utc
        )

    ownership.ownership_status = "released"
    ownership.released_at = datetime.now(timezone.utc)

    new_ownership = ProductOwnership(
        product_unit_id=product_unit.id,
        customer_id=transfer.to_customer_id,
        ownership_status="active",
        acquired_at=datetime.now(timezone.utc),
        released_at=None,
        source="transfer",
    )

    db.add(new_ownership)

    history = OwnershipHistory(
        product_unit_id=product_unit.id,
        from_customer_id=transfer.from_customer_id,
        to_customer_id=transfer.to_customer_id,
        event_type="transfer",
        reference_type="product_transfer",
        reference_id=transfer.id,
        notes=transfer.reason,
        transferred_at=datetime.now(timezone.utc),
    )

    db.add(history)

    transfer.status = "completed"
    transfer.approved_by_user_id = approved_by_user_id
    transfer.approved_at = datetime.now(timezone.utc)
    transfer.completed_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(transfer)

    return transfer


def reject_product_transfer(
    db: Session,
    transfer: ProductTransfer,
    rejected_by_user_id: uuid.UUID,
    rejection_reason: str,
) -> ProductTransfer:

    if transfer.status != "pending":
        raise ValueError(
            "Only pending transfers can be rejected."
        )

    if not rejection_reason.strip():
        raise ValueError(
            "Rejection reason is required."
        )

    transfer.status = "rejected"
    transfer.approved_by_user_id = None
    transfer.approved_at = None
    transfer.rejection_reason = rejection_reason

    db.commit()
    db.refresh(transfer)

    return transfer
