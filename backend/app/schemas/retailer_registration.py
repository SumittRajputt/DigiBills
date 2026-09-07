from pydantic import BaseModel, EmailStr, Field, model_validator


class RetailerRegistrationRequest(BaseModel):
    business_name: str = Field(
        min_length=2,
        max_length=200,
    )

    business_type: str = Field(
        min_length=2,
        max_length=100,
    )

    phone_number: str = Field(
        min_length=10,
        max_length=20,
    )

    email: EmailStr

    address: str = Field(
        min_length=5,
        max_length=1000,
    )

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
