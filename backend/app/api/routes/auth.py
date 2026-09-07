from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.authorization import require_permission
from app.api.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.auth import (
    ChangePasswordRequest,
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from app.schemas.retailer_registration import RetailerRegistrationRequest
from app.services.authorization_service import get_user_roles
from app.services.auth_service import (
    authenticate_user,
    change_user_password,
    create_user_token,
    register_user,
    register_retailer,
)


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(
    request: RegisterRequest,
    db: Session = Depends(get_db),
):
    try:
        user = register_user(
            db=db,
            full_name=request.full_name,
            phone_number=request.phone_number,
            email=str(request.email) if request.email else None,
            password=request.password,
        )

        roles = get_user_roles(
            db=db,
            user_id=user.id,
        )

        return UserResponse(
            id=str(user.id),
            phone_number=user.phone_number,
            email=user.email,
            status=user.status,
            is_phone_verified=user.is_phone_verified,
            roles=[role.name for role in roles],
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )


@router.post(
    "/retailer-register",
    status_code=status.HTTP_201_CREATED,
)
def register_retailer_account(
    request: RetailerRegistrationRequest,
    db: Session = Depends(get_db),
):
    try:
        user, retailer = register_retailer(
            db=db,
            phone_number=request.phone_number,
            email=str(request.email),
            password=request.password,
            business_name=request.business_name,
            business_type=request.business_type,
            business_phone_number=request.phone_number,
            business_email=str(request.email),
            address=request.address,
        )

        return {
            "message": (
                "Retailer registration submitted successfully. "
                "Your account is pending admin approval."
            ),
            "retailer_id": retailer.retailer_id,
            "status": retailer.status,
            "user_id": str(user.id),
        }

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )


@router.post(
    "/login",
    response_model=TokenResponse,
)
def login(
    request: LoginRequest,
    db: Session = Depends(get_db),
):
    user = authenticate_user(
        db=db,
        phone_number=request.phone_number,
        password=request.password,
        account_type=request.account_type,
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid phone number or password.",
        )

    token = create_user_token(user)

    return TokenResponse(
        access_token=token,
        token_type="bearer",
    )


@router.get(
    "/me",
    response_model=UserResponse,
)
def get_me(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    roles = get_user_roles(
        db=db,
        user_id=current_user.id,
    )

    return UserResponse(
        id=str(current_user.id),
        phone_number=current_user.phone_number,
        email=current_user.email,
        status=current_user.status,
        is_phone_verified=current_user.is_phone_verified,
        roles=[role.name for role in roles],
    )


@router.put(
    "/change-password",
)
def change_password(
    request: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        change_user_password(
            db=db,
            user=current_user,
            current_password=request.current_password,
            new_password=request.new_password,
        )

        return {
            "message": "Password changed successfully.",
        }

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )


@router.get(
    "/authorization-test",
)
def authorization_test(
    current_user: User = Depends(
        require_permission("retailer.manage")
    ),
):
    return {
        "status": "authorized",
        "user_id": str(current_user.id),
        "phone_number": current_user.phone_number,
        "permission": "retailer.manage",
    }