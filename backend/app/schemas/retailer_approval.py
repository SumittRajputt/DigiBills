from pydantic import BaseModel, Field


class RetailerRejectRequest(BaseModel):
    rejection_reason: str = Field(
        min_length=3,
        max_length=1000,
    )