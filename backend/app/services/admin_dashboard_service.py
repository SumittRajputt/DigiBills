from decimal import Decimal

from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.models.customer import Customer
from app.models.invoice import Invoice
from app.models.payment import Payment
from app.models.retailer import Retailer
from app.models.sales_return import SalesReturn


def get_admin_dashboard(db: Session) -> dict:
    total_retailers = db.scalar(
        select(func.count(Retailer.id))
    ) or 0

    active_retailers = db.scalar(
        select(func.count(Retailer.id)).where(
            Retailer.status == "active"
        )
    ) or 0

    pending_approvals = db.scalar(
        select(func.count(Retailer.id)).where(
            Retailer.status == "pending"
        )
    ) or 0

    total_customers = db.scalar(
        select(func.count(Customer.id))
    ) or 0

    total_invoices = db.scalar(
        select(func.count(Invoice.id))
    ) or 0

    total_sales = db.scalar(
        select(
            func.coalesce(
                func.sum(Invoice.total_amount),
                0,
            )
        ).where(
            Invoice.status == "active"
        )
    ) or Decimal("0.00")

    payments_collected = db.scalar(
        select(
            func.coalesce(
                func.sum(Payment.amount),
                0,
            )
        ).where(
            Payment.payment_status == "completed"
        )
    ) or Decimal("0.00")

    refunds = db.scalar(
        select(
            func.coalesce(
                func.sum(Payment.refund_amount),
                0,
            )
        )
    ) or Decimal("0.00")

    returns = db.scalar(
        select(
            func.coalesce(
                func.sum(SalesReturn.return_amount),
                0,
            )
        ).where(
            SalesReturn.status == "processed"
        )
    ) or Decimal("0.00")

    outstanding_amount = db.scalar(
        select(
            func.coalesce(
                func.sum(Invoice.total_amount),
                0,
            )
        ).where(
            Invoice.payment_status != "paid",
            Invoice.status == "active",
        )
    ) or Decimal("0.00")

    # -----------------------------
    # Sales overview
    # -----------------------------

    sales_rows = db.execute(
        select(
            func.date(Invoice.invoice_date).label("date"),
            func.coalesce(
                func.sum(Invoice.total_amount),
                0,
            ).label("amount"),
        )
        .where(
            Invoice.status == "active"
        )
        .group_by(
            func.date(Invoice.invoice_date)
        )
        .order_by(
            func.date(Invoice.invoice_date)
        )
    ).all()

    sales_overview = [
        {
            "date": str(row.date),
            "amount": str(row.amount),
        }
        for row in sales_rows
    ]

    # -----------------------------
    # Top retailers
    # -----------------------------

    retailer_rows = db.execute(
        select(
            Retailer.business_name,
            func.coalesce(
                func.sum(Invoice.total_amount),
                0,
            ).label("sales"),
        )
        .join(
            Invoice,
            Invoice.retailer_id == Retailer.id,
        )
        .where(
            Invoice.status == "active"
        )
        .group_by(
            Retailer.id,
            Retailer.business_name,
        )
        .order_by(
            desc("sales")
        )
        .limit(5)
    ).all()

    top_retailers = [
        {
            "business_name": row.business_name,
            "sales": str(row.sales),
        }
        for row in retailer_rows
    ]

    # -----------------------------
    # Payment methods
    # -----------------------------

    payment_rows = db.execute(
        select(
            Payment.payment_method,
            func.coalesce(
                func.sum(Payment.amount),
                0,
            ).label("amount"),
        )
        .where(
            Payment.payment_status == "completed"
        )
        .group_by(
            Payment.payment_method
        )
        .order_by(
            desc("amount")
        )
    ).all()

    payment_total = sum(
        (Decimal(str(row.amount)) for row in payment_rows),
        Decimal("0.00"),
    )

    payment_methods = []

    for row in payment_rows:
        amount = Decimal(str(row.amount))

        percentage = (
            (amount / payment_total) * Decimal("100")
            if payment_total > 0
            else Decimal("0.00")
        )

        payment_methods.append(
            {
                "method": row.payment_method,
                "amount": str(amount),
                "percentage": str(
                    percentage.quantize(Decimal("0.01"))
                ),
            }
        )

    # -----------------------------
    # Recent activity
    # -----------------------------

    activity_rows = db.execute(
        select(AuditLog)
        .order_by(
            AuditLog.created_at.desc()
        )
        .limit(10)
    ).scalars().all()

    recent_activity = [
        {
            "action": activity.action,
            "entity_type": activity.entity_type,
            "description": activity.description,
            "created_at": activity.created_at,
        }
        for activity in activity_rows
    ]

    return {
        "total_retailers": total_retailers,
        "active_retailers": active_retailers,
        "pending_approvals": pending_approvals,
        "total_customers": total_customers,
        "total_invoices": total_invoices,
        "total_sales": str(total_sales),
        "payments_collected": str(payments_collected),
        "refunds": str(refunds),
        "returns": str(returns),
        "outstanding_amount": str(outstanding_amount),
        "sales_overview": sales_overview,
        "top_retailers": top_retailers,
        "payment_methods": payment_methods,
        "recent_activity": recent_activity,
    }
