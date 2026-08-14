import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ProductOwnership(Base):
    __tablename__ = "product_ownerships"

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

    customer_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(
            "customers.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )

    ownership_status: Mapped[str] = mapped_column(
        String(30),
        default="active",
        nullable=False,
    )

    acquired_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )

    released_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    source: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )
