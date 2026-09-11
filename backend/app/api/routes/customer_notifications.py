from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.authorization import require_permission
from app.api.dependencies import get_db
from app.models.customer import Customer
from app.models.customer_notification import CustomerNotification
from app.models.user import User
from app.schemas.customer_notification import CustomerNotificationResponse
from app.services.customer_service import get_customer_by_user_id


router = APIRouter(
    prefix="/customer/notifications",
    tags=["Customer Notifications"],
)


@router.patch(
    "/{notification_id}/read",
    response_model=CustomerNotificationResponse,
)
def mark_customer_notification_read(
    notification_id: str,
    current_user: User = Depends(
        require_permission("customer.view")
    ),
    db: Session = Depends(get_db),
):
    customer = get_customer_by_user_id(
        db,
        current_user.id,
    )

    if customer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found for this user.",
        )

    if customer.status != "active":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Customer is not active.",
        )

    try:
        parsed_notification_id = __import__("uuid").UUID(
            notification_id
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid notification ID.",
        )

    notification = db.execute(
        select(CustomerNotification).where(
            CustomerNotification.id == parsed_notification_id,
            CustomerNotification.customer_id == customer.id,
        )
    ).scalar_one_or_none()

    if notification is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found.",
        )

    notification.is_read = True

    db.commit()
    db.refresh(notification)

    return CustomerNotificationResponse(
        id=str(notification.id),
        customer_id=str(notification.customer_id),
        notification_type=notification.notification_type,
        title=notification.title,
        message=notification.message,
        reference_type=notification.reference_type,
        reference_id=notification.reference_id,
        is_read=notification.is_read,
        created_at=notification.created_at,
    )


@router.get(
    "",
    response_model=list[CustomerNotificationResponse],
)
def list_customer_notifications(
    current_user: User = Depends(
        require_permission("customer.view")
    ),
    db: Session = Depends(get_db),
):
    customer = get_customer_by_user_id(
        db,
        current_user.id,
    )

    if customer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found for this user.",
        )

    if customer.status != "active":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Customer is not active.",
        )

    notifications = list(
        db.execute(
            select(CustomerNotification)
            .where(
                CustomerNotification.customer_id == customer.id,
            )
            .order_by(
                CustomerNotification.created_at.desc()
            )
        )
        .scalars()
        .all()
    )

    return [
        CustomerNotificationResponse(
            id=str(notification.id),
            customer_id=str(notification.customer_id),
            notification_type=notification.notification_type,
            title=notification.title,
            message=notification.message,
            reference_type=notification.reference_type,
            reference_id=notification.reference_id,
            is_read=notification.is_read,
            created_at=notification.created_at,
        )
        for notification in notifications
    ]
