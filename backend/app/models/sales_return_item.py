import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class SalesReturnItem(Base):
    __tablename__ = "sales_return_items"

    unit_mappings: Mapped[list["SalesReturnItemUnit"]] = relationship(
        "SalesReturnItemUnit",
        back_populates="sales_return_item",
        cascade="all, delete-orphan",
    )

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )

    sales_return_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("sales_returns.id", ondelete="CASCADE"),
        nullable=False,
    )

    invoice_item_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("invoice_items.id", ondelete="RESTRICT"),
        nullable=False,
    )

    product_variant_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("product_variants.id", ondelete="RESTRICT"),
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

    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False,
    )

    return_amount: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False,
    )

    restocking_fee: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        default=0,
        nullable=False,
    )

    refund_amount: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        default=0,
        nullable=False,
    )

    condition: Mapped[str] = mapped_column(
        String(30),
        default="good",
        nullable=False,
    )

    return_to_inventory: Mapped[bool] = mapped_column(
        default=True,
        nullable=False,
    )

    reason: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )