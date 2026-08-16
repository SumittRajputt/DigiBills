from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.authorization import require_role
from app.api.dependencies import get_db
from app.models.user import User
from app.schemas.admin_dashboard import AdminDashboardResponse
from app.services.admin_dashboard_service import get_admin_dashboard


router = APIRouter(
    prefix="/admin",
    tags=["Admin Dashboard"],
)


@router.get(
    "/dashboard",
    response_model=AdminDashboardResponse,
)
def get_admin_dashboard_endpoint(
    current_user: User = Depends(
        require_role("super_admin")
    ),
    db: Session = Depends(get_db),
):
    return get_admin_dashboard(db)


@router.get(
    "/purchase-returns",
)
def get_admin_purchase_returns_endpoint(
    current_user: User = Depends(
        require_role("super_admin")
    ),
    db: Session = Depends(get_db),
):
    from app.services.purchase_return_service import (
        get_all_purchase_returns,
    )

    returns = get_all_purchase_returns(db)

    return [
        {
            "id": str(item.id),
            "return_id": item.return_id,
            "purchase_order_id": str(item.purchase_order_id),
            "retailer_id": str(item.retailer_id),
            "supplier_id": str(item.supplier_id),
            "location_id": str(item.location_id),
            "processed_by_user_id": (
                str(item.processed_by_user_id)
                if item.processed_by_user_id
                else None
            ),
            "return_amount": item.return_amount,
            "status": item.status,
            "reason": item.reason,
            "notes": item.notes,
            "requested_at": item.requested_at,
            "processed_at": item.processed_at,
            "created_at": item.created_at,
            "updated_at": item.updated_at,
        }
        for item in returns
    ]


@router.get(
    "/warranties",
)
def get_admin_warranties_endpoint(
    current_user: User = Depends(
        require_role("super_admin")
    ),
    db: Session = Depends(get_db),
):
    from app.services.warranty_service import (
        get_all_warranties,
    )

    warranties = get_all_warranties(db)

    return [
        {
            "id": str(item.id),
            "warranty_id": item.warranty_id,
            "invoice_id": str(item.invoice_id),
            "product_variant_id": str(
                item.product_variant_id
            ),
            "customer_id": str(item.customer_id),
            "start_date": item.start_date,
            "end_date": item.end_date,
            "duration_months": item.duration_months,
            "is_transferable": item.is_transferable,
            "status": item.status,
            "created_at": item.created_at,
            "updated_at": item.updated_at,
        }
        for item in warranties
    ]


@router.get(
    "/reports",
)
def get_admin_reports_endpoint(
    current_user: User = Depends(
        require_role("super_admin")
    ),
    db: Session = Depends(get_db),
):
    from app.services.report_service import (
        get_admin_reports,
    )

    return get_admin_reports(db)


@router.get(
    "/audit-logs",
)
def get_admin_audit_logs_endpoint(
    current_user: User = Depends(
        require_role("super_admin")
    ),
    db: Session = Depends(get_db),
):
    from app.services.audit_log_service import (
        get_all_audit_logs,
    )

    audit_logs = get_all_audit_logs(db)

    return [
        {
            "id": str(item.id),
            "retailer_id": (
                str(item.retailer_id)
                if item.retailer_id
                else None
            ),
            "user_id": (
                str(item.user_id)
                if item.user_id
                else None
            ),
            "action": item.action,
            "entity_type": item.entity_type,
            "entity_id": (
                str(item.entity_id)
                if item.entity_id
                else None
            ),
            "description": item.description,
            "ip_address": item.ip_address,
            "user_agent": item.user_agent,
            "created_at": item.created_at,
        }
        for item in audit_logs
    ]
