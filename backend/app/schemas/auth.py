from typing import Optional

from pydantic import BaseModel, EmailStr, Field, model_validator


class RegisterRequest(BaseModel):
    full_name: str = Field(
        min_length=2,
        max_length=150,
    )

    phone_number: str = Field(
        min_length=10,
        max_length=20,
    )

    email: Optional[EmailStr] = None

    password: str = Field(
        min_length=8,
        max_length=72,
    )

    confirm_password: str = Field(
        min_length=8,
        max_length=72,
    )

    @model_validator(mode="after")
    def passwords_match(self):
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match.")
        return self


class LoginRequest(BaseModel):
    phone_number: str
    password: str
    account_type: str = Field(
        pattern="^(admin|retailer|customer|employee|salesman)$"
    )


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(
        min_length=8,
        max_length=72,
    )

    new_password: str = Field(
        min_length=8,
        max_length=72,
    )


class TokenResponse(BaseModel):
    access_token: str
    token_type: str


class UserResponse(BaseModel):
    id: str
    phone_number: str
    email: Optional[str] = None
    status: str
    is_phone_verified: bool
    roles: list[str]


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str = Field(min_length=20)
    new_password: str = Field(
        min_length=8,
        max_length=72,
    )
    confirm_password: str = Field(
        min_length=8,
        max_length=72,
    )

    @model_validator(mode="after")
    def passwords_match(self):
        if self.new_password != self.confirm_password:
            raise ValueError("Passwords do not match.")
        return self

