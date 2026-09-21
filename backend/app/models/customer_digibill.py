import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class CustomerDigiBill(Base):
    __tablename__ = "customer_digibills"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )

    digibill_id: Mapped[str] = mapped_column(
        String(20),
        unique=True,
        index=True,
        nullable=False,
    )

    uploaded_bill_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(
            "customer_uploaded_bills.id",
            ondelete="RESTRICT",
        ),
        unique=True,
        index=True,
        nullable=False,
    )

    customer_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(
            "customers.id",
            ondelete="RESTRICT",
        ),
        index=True,
        nullable=False,
    )

    invoice_number: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )

    invoice_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    retailer_data: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
    )

    customer_data: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
    )

    products: Mapped[list] = mapped_column(
        JSONB,
        nullable=False,
    )

    totals: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
    )

    payment: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
    )

    warranty_evidence: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
    )

    confidence_scores: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
    )

    extraction_notes: Mapped[list] = mapped_column(
        JSONB,
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="confirmed",
    )

    confirmed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
