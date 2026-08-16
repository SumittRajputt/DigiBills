from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class UserResponse(BaseModel):
    id: str
    phone_number: str
    email: Optional[str] = None
    status: str
    is_phone_verified: bool
    roles: List[str]
    last_login_at: Optional[datetime] = None
    created_at: datetime
