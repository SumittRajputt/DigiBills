import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class PurchaseReturn(Base):
    __tablename__ = "purchase_returns"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )

    return_id: Mapped[str] = mapped_column(
        String(30),
        unique=True,
        index=True,
        nullable=False,
    )

    purchase_order_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(
            "purchase_orders.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )

    retailer_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(
            "retailers.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )

    supplier_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(
            "suppliers.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )

    location_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(
            "inventory_locations.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )

    processed_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )

    return_amount: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        default="requested",
        nullable=False,
    )

    reason: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    requested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )

    processed_at: Mapped[Optional[datetime]] = mapped_column(
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