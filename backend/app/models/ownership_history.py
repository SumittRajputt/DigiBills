import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class OwnershipHistory(Base):
    __tablename__ = "ownership_history"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )

    product_unit_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(
            "product_units.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )

    from_customer_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey(
            "customers.id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )

    to_customer_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(
            "customers.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )

    event_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    reference_type: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )

    reference_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        nullable=True,
    )

    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    transferred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )
