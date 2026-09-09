from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.authorization import require_role
from app.api.dependencies import get_db
from app.models.user import User
from app.schemas.brand_settings import (
    BrandSettingsResponse,
    BrandSettingsUpdate,
)
from app.services.brand_settings_service import (
    get_brand_settings,
    update_brand_settings,
)


router = APIRouter(tags=["Brand Settings"])


@router.get(
    "/brand-settings",
    response_model=BrandSettingsResponse,
)
def get_brand_settings_endpoint(
    db: Session = Depends(get_db),
):
    try:
        brand = get_brand_settings(db)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    return {
        "id": str(brand.id),
        "company_name": brand.company_name,
        "logo_url": brand.logo_url,
        "primary_color": brand.primary_color,
        "secondary_color": brand.secondary_color,
        "accent_color": brand.accent_color,
        "login_tagline": brand.login_tagline,
        "created_at": brand.created_at,
        "updated_at": brand.updated_at,
    }


@router.put(
    "/admin/brand-settings",
    response_model=BrandSettingsResponse,
)
def update_brand_settings_endpoint(
    data: BrandSettingsUpdate,
    current_user: User = Depends(
        require_role("super_admin")
    ),
    db: Session = Depends(get_db),
):
    brand = update_brand_settings(db, data)

    return {
        "id": str(brand.id),
        "company_name": brand.company_name,
        "logo_url": brand.logo_url,
        "primary_color": brand.primary_color,
        "secondary_color": brand.secondary_color,
        "accent_color": brand.accent_color,
        "login_tagline": brand.login_tagline,
        "created_at": brand.created_at,
        "updated_at": brand.updated_at,
    }
