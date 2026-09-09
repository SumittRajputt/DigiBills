from sqlalchemy.orm import Session

from app.models.brand_settings import BrandSettings
from app.schemas.brand_settings import BrandSettingsUpdate


def get_brand_settings(db: Session) -> BrandSettings:
    """Return the current application branding settings."""
    brand = db.query(BrandSettings).first()

    if brand is None:
        raise ValueError("Brand settings have not been configured.")

    return brand


def update_brand_settings(
    db: Session,
    data: BrandSettingsUpdate,
) -> BrandSettings:
    """Update the current application branding settings."""
    brand = db.query(BrandSettings).first()

    if brand is None:
        brand = BrandSettings()
        db.add(brand)

    brand.company_name = data.company_name.strip()
    brand.logo_url = data.logo_url.strip() if data.logo_url else None
    brand.primary_color = data.primary_color.strip()
    brand.secondary_color = data.secondary_color.strip()
    brand.accent_color = data.accent_color.strip()
    brand.login_tagline = data.login_tagline.strip()

    db.commit()
    db.refresh(brand)

    return brand
