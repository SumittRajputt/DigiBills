from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    phone_number: str = Field(
        min_length=10,
        max_length=20,
    )

    email: Optional[EmailStr] = None

    password: str = Field(
        min_length=8,
        max_length=72,
    )


class LoginRequest(BaseModel):
    phone_number: str = Field(
        min_length=10,
        max_length=20,
    )

    password: str = Field(
        min_length=8,
        max_length=72,
    )


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: str
    phone_number: str
    email: Optional[str] = None
    status: str
    is_phone_verified: bool