import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class InvoiceItemUnit(Base):
    __tablename__ = "invoice_item_units"

    invoice_item: Mapped["InvoiceItem"] = relationship(
        "InvoiceItem",
        back_populates="unit_mappings",
    )

    product_unit: Mapped["ProductUnit"] = relationship(
        "ProductUnit",
    )

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )

    invoice_item_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(
            "invoice_items.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    product_unit_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(
            "product_units.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )
