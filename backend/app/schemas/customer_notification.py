from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class CustomerNotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    customer_id: str
    notification_type: str
    title: str
    message: str
    reference_type: Optional[str] = None
    reference_id: Optional[str] = None
    is_read: bool
    created_at: datetime
