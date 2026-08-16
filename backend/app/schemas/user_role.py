from pydantic import BaseModel, Field


class UserRoleRequest(BaseModel):
    role_name: str = Field(
        min_length=2,
        max_length=100,
    )
