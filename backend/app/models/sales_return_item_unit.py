import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class SalesReturnItemUnit(Base):
    __tablename__ = "sales_return_item_units"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )

    sales_return_item_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(
            "sales_return_items.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    sales_return_item: Mapped["SalesReturnItem"] = relationship(
        "SalesReturnItem",
        back_populates="unit_mappings",
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
