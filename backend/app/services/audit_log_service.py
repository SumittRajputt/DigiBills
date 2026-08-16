import uuid
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog


def create_audit_log(
    db: Session,
    retailer_id: Optional[uuid.UUID],
    user_id: Optional[uuid.UUID],
    action: str,
    entity_type: str,
    entity_id: Optional[uuid.UUID] = None,
    description: Optional[str] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> AuditLog:
    audit_log = AuditLog(
        retailer_id=retailer_id,
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        description=description,
        ip_address=ip_address,
        user_agent=user_agent,
    )

    db.add(audit_log)
    db.flush()

    return audit_log


def get_audit_logs_for_retailer(
    db: Session,
    retailer_id: uuid.UUID,
) -> List[AuditLog]:
    statement = (
        select(AuditLog)
        .where(
            AuditLog.retailer_id == retailer_id
        )
        .order_by(
            AuditLog.created_at.desc()
        )
    )

    return list(
        db.execute(statement).scalars().all()
    )


def get_audit_log_for_retailer(
    db: Session,
    audit_log_id: uuid.UUID,
    retailer_id: uuid.UUID,
) -> Optional[AuditLog]:
    statement = select(AuditLog).where(
        AuditLog.id == audit_log_id,
        AuditLog.retailer_id == retailer_id,
    )

    return db.execute(
        statement
    ).scalar_one_or_none()


def get_all_audit_logs(
    db: Session,
) -> List[AuditLog]:
    statement = (
        select(AuditLog)
        .order_by(
            AuditLog.created_at.desc()
        )
    )

    return list(
        db.execute(statement).scalars().all()
    )
