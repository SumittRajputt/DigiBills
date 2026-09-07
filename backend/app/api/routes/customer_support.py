import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.authorization import require_permission
from app.api.dependencies import get_db
from app.models.support_ticket import SupportTicket
from app.models.user import User
from app.schemas.support_ticket import (
    SupportTicketCreateRequest,
    SupportTicketResponse,
)
from app.services.customer_service import get_customer_by_user_id


router = APIRouter(
    prefix="/customer/support",
    tags=["Customer Support"],
)


def ticket_to_response(
    ticket: SupportTicket,
) -> SupportTicketResponse:
    return SupportTicketResponse(
        id=str(ticket.id),
        ticket_id=ticket.ticket_id,
        customer_id=str(ticket.customer_id),
        subject=ticket.subject,
        description=ticket.description,
        status=ticket.status,
        priority=ticket.priority,
        category=ticket.category,
        resolution=ticket.resolution,
        created_at=ticket.created_at,
        updated_at=ticket.updated_at,
    )


@router.get(
    "",
    response_model=list[SupportTicketResponse],
)
def list_customer_support_tickets(
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

    tickets = db.execute(
        select(SupportTicket)
        .where(
            SupportTicket.customer_id == customer.id
        )
        .order_by(
            SupportTicket.created_at.desc()
        )
    ).scalars().all()

    return [
        ticket_to_response(ticket)
        for ticket in tickets
    ]


@router.post(
    "",
    response_model=SupportTicketResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_customer_support_ticket(
    request: SupportTicketCreateRequest,
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

    priority = request.priority.lower().strip()

    if priority not in {
        "low",
        "normal",
        "high",
        "urgent",
    }:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid support ticket priority.",
        )

    ticket = SupportTicket(
        ticket_id=f"TKT-{uuid.uuid4().hex[:10].upper()}",
        customer_id=customer.id,
        subject=request.subject.strip(),
        description=request.description.strip(),
        status="open",
        priority=priority,
        category=(
            request.category.strip()
            if request.category
            else None
        ),
        resolution=None,
    )

    db.add(ticket)
    db.commit()
    db.refresh(ticket)

    return ticket_to_response(ticket)
