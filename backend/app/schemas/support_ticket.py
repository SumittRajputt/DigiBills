from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class SupportTicketCreateRequest(BaseModel):
    subject: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1)
    priority: str = "normal"
    category: Optional[str] = None


class SupportTicketResponse(BaseModel):
    id: str
    ticket_id: str
    customer_id: str
    subject: str
    description: str
    status: str
    priority: str
    category: Optional[str]
    resolution: Optional[str]
    created_at: datetime
    updated_at: datetime
