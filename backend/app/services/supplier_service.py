import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.retailer import Retailer
from app.models.supplier import Supplier


def get_supplier_by_id(
    db: Session,
    supplier_id: uuid.UUID,
) -> Optional[Supplier]:
    statement = select(Supplier).where(
        Supplier.id == supplier_id
    )

    return db.execute(
        statement
    ).scalar_one_or_none()


def get_supplier_by_supplier_id(
    db: Session,
    supplier_id: str,
) -> Optional[Supplier]:
    statement = select(Supplier).where(
        Supplier.supplier_id == supplier_id
    )

    return db.execute(
        statement
    ).scalar_one_or_none()


def get_supplier_by_name(
    db: Session,
    retailer_id: uuid.UUID,
    name: str,
) -> Optional[Supplier]:
    statement = select(Supplier).where(
        Supplier.retailer_id == retailer_id,
        Supplier.name == name,
    )

    return db.execute(
        statement
    ).scalar_one_or_none()


def get_suppliers_for_retailer(
    db: Session,
    retailer_id: uuid.UUID,
) -> list[Supplier]:
    statement = (
        select(Supplier)
        .where(
            Supplier.retailer_id == retailer_id
        )
        .order_by(Supplier.name.asc())
    )

    return list(
        db.execute(statement).scalars().all()
    )


def create_supplier(
    db: Session,
    retailer: Retailer,
    name: str,
    contact_person: Optional[str] = None,
    phone_number: Optional[str] = None,
    email: Optional[str] = None,
    address: Optional[str] = None,
    tax_identifier: Optional[str] = None,
) -> Supplier:

    if retailer.status != "active":
        raise ValueError(
            "Retailer is not active."
        )

    name = name.strip()

    if not name:
        raise ValueError(
            "Supplier name is required."
        )

    existing_supplier = get_supplier_by_name(
        db,
        retailer.id,
        name,
    )

    if existing_supplier:
        raise ValueError(
            "A supplier with this name already exists."
        )

    supplier = Supplier(
        supplier_id=(
            f"SUP-{uuid.uuid4().hex[:10].upper()}"
        ),
        retailer_id=retailer.id,
        name=name,
        contact_person=contact_person,
        phone_number=phone_number,
        email=email,
        address=address,
        tax_identifier=tax_identifier,
        is_active=True,
    )

    db.add(supplier)
    db.commit()
    db.refresh(supplier)

    return supplier


def update_supplier_status(
    db: Session,
    supplier: Supplier,
    is_active: bool,
) -> Supplier:

    supplier.is_active = is_active

    db.commit()
    db.refresh(supplier)

    return supplier