import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.retailer import Retailer
from app.models.user import User


def get_retailer_by_id(
    db: Session,
    retailer_id: uuid.UUID,
) -> Optional[Retailer]:
    statement = select(Retailer).where(
        Retailer.id == retailer_id
    )

    return db.execute(
        statement
    ).scalar_one_or_none()


def get_retailer_by_retailer_id(
    db: Session,
    retailer_id: str,
) -> Optional[Retailer]:
    statement = select(Retailer).where(
        Retailer.retailer_id == retailer_id
    )

    return db.execute(
        statement
    ).scalar_one_or_none()


def get_retailer_by_owner(
    db: Session,
    owner_user_id: uuid.UUID,
) -> Optional[Retailer]:
    statement = select(Retailer).where(
        Retailer.owner_user_id == owner_user_id
    )

    return db.execute(
        statement
    ).scalar_one_or_none()


def generate_retailer_id() -> str:
    return f"RET-{uuid.uuid4().hex[:10].upper()}"


def create_retailer(
    db: Session,
    owner_user: User,
    business_name: str,
    business_type: str,
    phone_number: str,
    email: Optional[str],
    address: Optional[str],
) -> Retailer:

    existing_retailer = get_retailer_by_owner(
        db,
        owner_user.id,
    )

    if existing_retailer:
        raise ValueError(
            "This user already owns a retailer."
        )

    retailer = Retailer(
        retailer_id=generate_retailer_id(),
        owner_user_id=owner_user.id,
        business_name=business_name,
        business_type=business_type,
        phone_number=phone_number,
        email=email,
        address=address,
        status="pending",
    )

    db.add(retailer)
    db.commit()
    db.refresh(retailer)

    return retailer

def get_all_retailers(
    db: Session,
) -> list[Retailer]:
    statement = (
        select(Retailer)
        .order_by(Retailer.created_at.desc())
    )

    return list(
        db.execute(statement).scalars().all()
    )


def update_retailer(
    db: Session,
    retailer: Retailer,
    business_name: str,
    business_type: str,
    phone_number: str,
    email: Optional[str],
    address: Optional[str],
) -> Retailer:
    retailer.business_name = business_name.strip()
    retailer.business_type = (
        business_type.strip() if business_type else None
    )
    retailer.phone_number = phone_number.strip()
    retailer.email = email
    retailer.address = address.strip() if address else None

    db.commit()
    db.refresh(retailer)

    return retailer
