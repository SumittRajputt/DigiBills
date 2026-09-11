from typing import Optional
import uuid

from sqlalchemy.orm import Session

from app.models.customer_notification import CustomerNotification


def create_customer_notification(
    db: Session,
    customer_id: uuid.UUID,
    title: str,
    message: str,
    notification_type: str = "general",
    reference_type: Optional[str] = None,
    reference_id: Optional[str] = None,
) -> CustomerNotification:
    notification = CustomerNotification(
        customer_id=customer_id,
        notification_type=notification_type,
        title=title,
        message=message,
        reference_type=reference_type,
        reference_id=reference_id,
        is_read=False,
    )

    db.add(notification)
    db.flush()

    return notification
