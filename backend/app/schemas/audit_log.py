from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class AuditLogResponse(BaseModel):
    id: str
    retailer_id: Optional[str]
    user_id: Optional[str]
    action: str
    entity_type: str
    entity_id: Optional[str]
    description: Optional[str]
    ip_address: Optional[str]
    user_agent: Optional[str]
    created_at: datetime
