import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ProductTransfer(Base):
    __tablename__ = "product_transfers"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )

    transfer_id: Mapped[str] = mapped_column(
        String(30),
        unique=True,
        index=True,
        nullable=False,
    )

    product_unit_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(
            "product_units.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )

    from_customer_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(
            "customers.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )

    to_customer_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(
            "customers.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )

    requested_by_user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )

    approved_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        default="pending",
        nullable=False,
    )

    reason: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    rejection_reason: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    requested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )

    approved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )
