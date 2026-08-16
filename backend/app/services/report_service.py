from decimal import Decimal

from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.models.invoice import Invoice
from app.models.payment import Payment
from app.models.purchase_return import PurchaseReturn
from app.models.retailer import Retailer
from app.models.sales_return import SalesReturn


def get_admin_reports(db: Session) -> dict:
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

    total_invoices = db.scalar(
        select(func.count(Invoice.id)).where(
            Invoice.status == "active"
        )
    ) or 0

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

    total_refunds = db.scalar(
        select(
            func.coalesce(
                func.sum(Payment.refund_amount),
                0,
            )
        )
    ) or Decimal("0.00")

    sales_returns = db.scalar(
        select(
            func.coalesce(
                func.sum(SalesReturn.return_amount),
                0,
            )
        ).where(
            SalesReturn.status == "processed"
        )
    ) or Decimal("0.00")

    purchase_returns = db.scalar(
        select(
            func.coalesce(
                func.sum(PurchaseReturn.return_amount),
                0,
            )
        ).where(
            PurchaseReturn.status == "processed"
        )
    ) or Decimal("0.00")

    average_invoice_value = (
        total_sales / total_invoices
        if total_invoices
        else Decimal("0.00")
    )

    retailer_rows = db.execute(
        select(
            Retailer.business_name,
            Retailer.status,
            func.count(Invoice.id).label("invoice_count"),
            func.coalesce(
                func.sum(Invoice.total_amount),
                0,
            ).label("sales"),
        )
        .outerjoin(
            Invoice,
            Invoice.retailer_id == Retailer.id,
        )
        .where(
            Invoice.status == "active"
        )
        .group_by(
            Retailer.id,
            Retailer.business_name,
            Retailer.status,
        )
        .order_by(
            desc("sales")
        )
        .limit(10)
    ).all()

    retailer_performance = [
        {
            "business_name": row.business_name,
            "status": row.status,
            "invoice_count": row.invoice_count,
            "sales": str(row.sales),
        }
        for row in retailer_rows
    ]

    sales_rows = db.execute(
        select(
            func.date(Invoice.invoice_date).label("date"),
            func.count(Invoice.id).label("invoice_count"),
            func.coalesce(
                func.sum(Invoice.total_amount),
                0,
            ).label("sales"),
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

    sales_trend = [
        {
            "date": str(row.date),
            "invoice_count": row.invoice_count,
            "sales": str(row.sales),
        }
        for row in sales_rows
    ]

    payment_rows = db.execute(
        select(
            Payment.payment_method,
            func.count(Payment.id).label("payment_count"),
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

    payment_methods = [
        {
            "method": row.payment_method,
            "payment_count": row.payment_count,
            "amount": str(row.amount),
        }
        for row in payment_rows
    ]

    return {
        "total_sales": str(total_sales),
        "total_invoices": total_invoices,
        "average_invoice_value": str(
            average_invoice_value
        ),
        "payments_collected": str(
            payments_collected
        ),
        "total_refunds": str(total_refunds),
        "sales_returns": str(sales_returns),
        "purchase_returns": str(purchase_returns),
        "retailer_performance": retailer_performance,
        "sales_trend": sales_trend,
        "payment_methods": payment_methods,
    }
