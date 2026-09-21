import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class CustomerBillExtraction(Base):
    __tablename__ = "customer_bill_extractions"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )

    uploaded_bill_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(
            "customer_uploaded_bills.id",
            ondelete="CASCADE",
        ),
        unique=True,
        index=True,
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="pending",
    )

    raw_text: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    structured_data: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
    )

    document_status: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
    )

    validation_score: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )

    validation_reasons: Mapped[Optional[list]] = mapped_column(
        JSONB,
        nullable=True,
    )

    digibill_eligible: Mapped[Optional[bool]] = mapped_column(
        Boolean,
        nullable=True,
    )

    page_count: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )

    extraction_engine: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )

    extraction_model: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )

    error_message: Mapped[Optional[str]] = mapped_column(
        Text,
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
