import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.authorization import require_permission
from app.api.dependencies import get_db
from app.models.user import User
from app.schemas.audit_log import AuditLogResponse
from app.services.audit_log_service import (
    get_audit_log_for_retailer,
    get_audit_logs_for_retailer,
)
from app.services.retailer_service import (
    get_retailer_by_owner,
)


router = APIRouter(
    prefix="/audit-logs",
    tags=["Audit Logs"],
)


def audit_log_to_response(
    audit_log,
) -> AuditLogResponse:
    return AuditLogResponse(
        id=str(audit_log.id),
        retailer_id=(
            str(audit_log.retailer_id)
            if audit_log.retailer_id
            else None
        ),
        user_id=(
            str(audit_log.user_id)
            if audit_log.user_id
            else None
        ),
        action=audit_log.action,
        entity_type=audit_log.entity_type,
        entity_id=(
            str(audit_log.entity_id)
            if audit_log.entity_id
            else None
        ),
        description=audit_log.description,
        ip_address=audit_log.ip_address,
        user_agent=audit_log.user_agent,
        created_at=audit_log.created_at,
    )


@router.get(
    "",
    response_model=list[AuditLogResponse],
)
def list_audit_logs_endpoint(
    current_user: User = Depends(
        require_permission("audit_log.view")
    ),
    db: Session = Depends(get_db),
):
    retailer = get_retailer_by_owner(
        db,
        current_user.id,
    )

    if retailer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Retailer not found.",
        )

    audit_logs = get_audit_logs_for_retailer(
        db,
        retailer.id,
    )

    return [
        audit_log_to_response(audit_log)
        for audit_log in audit_logs
    ]


@router.get(
    "/{audit_log_id}",
    response_model=AuditLogResponse,
)
def get_audit_log_endpoint(
    audit_log_id: str,
    current_user: User = Depends(
        require_permission("audit_log.view")
    ),
    db: Session = Depends(get_db),
):
    retailer = get_retailer_by_owner(
        db,
        current_user.id,
    )

    if retailer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audit log not found.",
        )

    try:
        parsed_id = uuid.UUID(audit_log_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid audit log ID.",
        )

    audit_log = get_audit_log_for_retailer(
        db,
        parsed_id,
        retailer.id,
    )

    if audit_log is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audit log not found.",
        )

    return audit_log_to_response(audit_log)
