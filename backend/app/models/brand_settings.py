import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class BrandSettings(Base):
    __tablename__ = "brand_settings"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )

    company_name: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
        default="DigiBills",
    )

    logo_url: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    primary_color: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="#7352D6",
    )

    secondary_color: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="#5E42B8",
    )

    accent_color: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="#F2EDFF",
    )

    login_tagline: Mapped[str] = mapped_column(
        String(180),
        nullable=False,
        default="Your Bills. Always With You",
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
