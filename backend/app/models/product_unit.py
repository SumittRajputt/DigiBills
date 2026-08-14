import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ProductUnit(Base):
    __tablename__ = "product_units"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )

    product_variant_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(
            "product_variants.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )

    serial_number: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        index=True,
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        default="in_stock",
        nullable=False,
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
