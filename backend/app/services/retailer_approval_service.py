from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.retailer import Retailer
from app.models.user import User


def approve_retailer(
    db: Session,
    retailer: Retailer,
    approved_by: User,
) -> Retailer:
    if retailer.status == "active":
        raise ValueError(
            "Retailer is already active."
        )

    if retailer.status == "rejected":
        raise ValueError(
            "A rejected retailer cannot be approved directly."
        )

    if retailer.status != "pending":
        raise ValueError(
            f"Cannot approve retailer with status "
            f"'{retailer.status}'."
        )

    retailer.status = "active"
    retailer.approved_at = datetime.utcnow()
    retailer.approved_by = approved_by.id
    retailer.rejection_reason = None

    db.add(retailer)
    db.commit()
    db.refresh(retailer)

    return retailer


def reject_retailer(
    db: Session,
    retailer: Retailer,
    rejected_by: User,
    rejection_reason: str,
) -> Retailer:
    if retailer.status == "active":
        raise ValueError(
            "An active retailer cannot be rejected."
        )

    if retailer.status == "rejected":
        raise ValueError(
            "Retailer is already rejected."
        )

    if retailer.status != "pending":
        raise ValueError(
            f"Cannot reject retailer with status "
            f"'{retailer.status}'."
        )

    reason = rejection_reason.strip()

    if not reason:
        raise ValueError(
            "Rejection reason is required."
        )

    retailer.status = "rejected"
    retailer.approved_at = None
    retailer.approved_by = rejected_by.id
    retailer.rejection_reason = reason

    db.add(retailer)
    db.commit()
    db.refresh(retailer)

    return retailer