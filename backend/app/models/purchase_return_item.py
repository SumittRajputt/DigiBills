import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class PurchaseReturnItem(Base):
    __tablename__ = "purchase_return_items"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )

    purchase_return_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(
            "purchase_returns.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    purchase_order_item_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(
            "purchase_order_items.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )

    product_variant_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(
            "product_variants.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )

    product_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    sku: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )

    quantity: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    unit_cost: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False,
    )

    return_amount: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False,
    )

    reason: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )

    condition: Mapped[str] = mapped_column(
        String(30),
        default="good",
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )