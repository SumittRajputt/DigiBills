from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class BrandSettingsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    company_name: str
    logo_url: Optional[str] = None
    primary_color: str
    secondary_color: str
    accent_color: str
    login_tagline: str
    created_at: datetime
    updated_at: datetime


class BrandSettingsUpdate(BaseModel):
    company_name: str = Field(
        min_length=1,
        max_length=120,
    )
    logo_url: Optional[str] = None
    primary_color: str = Field(
        min_length=4,
        max_length=20,
    )
    secondary_color: str = Field(
        min_length=4,
        max_length=20,
    )
    accent_color: str = Field(
        min_length=4,
        max_length=20,
    )
    login_tagline: str = Field(
        min_length=1,
        max_length=180,
    )
