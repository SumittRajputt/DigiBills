from decimal import Decimal

from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.models.customer import Customer
from app.models.invoice import Invoice
from app.models.payment import Payment
from app.models.inventory_item import InventoryItem
from app.models.product_variant import ProductVariant


def get_retailer_dashboard(
    db: Session,
    retailer_id,
) -> dict:

    # ---------------------------------------------------------
    # BASIC COUNTS
    # ---------------------------------------------------------

    total_customers = db.scalar(
        select(func.count(func.distinct(Customer.id)))
        .join(
            Invoice,
            Invoice.customer_id == Customer.id,
        )
        .where(
            Invoice.retailer_id == retailer_id,
            Invoice.status == "active",
        )
    ) or 0

    total_invoices = db.scalar(
        select(func.count(Invoice.id))
        .where(
            Invoice.retailer_id == retailer_id,
            Invoice.status == "active",
        )
    ) or 0

    # ---------------------------------------------------------
    # SALES
    # ---------------------------------------------------------

    total_sales = db.scalar(
        select(
            func.coalesce(
                func.sum(Invoice.total_amount),
                0,
            )
        ).where(
            Invoice.retailer_id == retailer_id,
            Invoice.status == "active",
        )
    ) or Decimal("0.00")

    # ---------------------------------------------------------
    # PAYMENTS
    # ---------------------------------------------------------

    payments_collected = db.scalar(
        select(
            func.coalesce(
                func.sum(Payment.amount),
                0,
            )
        )
        .join(
            Invoice,
            Payment.invoice_id == Invoice.id,
        )
        .where(
            Invoice.retailer_id == retailer_id,
            Payment.payment_status == "completed",
        )
    ) or Decimal("0.00")

    # ---------------------------------------------------------
    # OUTSTANDING
    # ---------------------------------------------------------

    outstanding_amount = db.scalar(
        select(
            func.coalesce(
                func.sum(
                    Invoice.total_amount
                    - func.coalesce(
                        select(
                            func.sum(Payment.amount)
                        )
                        .where(
                            Payment.invoice_id == Invoice.id,
                            Payment.payment_status == "completed",
                        )
                        .scalar_subquery(),
                        0,
                    )
                ),
                0,
            )
        ).where(
            Invoice.retailer_id == retailer_id,
            Invoice.status == "active",
            Invoice.payment_status != "paid",
        )
    ) or Decimal("0.00")

    # ---------------------------------------------------------
    # PAYMENT STATUS COUNTS
    # ---------------------------------------------------------

    paid_invoices = db.scalar(
        select(func.count(Invoice.id))
        .where(
            Invoice.retailer_id == retailer_id,
            Invoice.status == "active",
            Invoice.payment_status == "paid",
        )
    ) or 0

    partial_invoices = db.scalar(
        select(func.count(Invoice.id))
        .where(
            Invoice.retailer_id == retailer_id,
            Invoice.status == "active",
            Invoice.payment_status == "partial",
        )
    ) or 0

    unpaid_invoices = db.scalar(
        select(func.count(Invoice.id))
        .where(
            Invoice.retailer_id == retailer_id,
            Invoice.status == "active",
            Invoice.payment_status == "unpaid",
        )
    ) or 0

    # ---------------------------------------------------------
    # SALES OVERVIEW
    # ---------------------------------------------------------

    sales_rows = db.execute(
        select(
            func.date(
                Invoice.invoice_date
            ).label("date"),
            func.coalesce(
                func.sum(Invoice.total_amount),
                0,
            ).label("amount"),
        )
        .where(
            Invoice.retailer_id == retailer_id,
            Invoice.status == "active",
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

    # ---------------------------------------------------------
    # PAYMENT METHODS
    # ---------------------------------------------------------

    payment_rows = db.execute(
        select(
            Payment.payment_method,
            func.coalesce(
                func.sum(Payment.amount),
                0,
            ).label("amount"),
        )
        .join(
            Invoice,
            Payment.invoice_id == Invoice.id,
        )
        .where(
            Invoice.retailer_id == retailer_id,
            Payment.payment_status == "completed",
        )
        .group_by(
            Payment.payment_method
        )
        .order_by(
            desc("amount")
        )
    ).all()

    payment_total = sum(
        (
            Decimal(str(row.amount))
            for row in payment_rows
        ),
        Decimal("0.00"),
    )

    payment_methods = []

    for row in payment_rows:
        amount = Decimal(str(row.amount))

        percentage = (
            (amount / payment_total)
            * Decimal("100")
            if payment_total > 0
            else Decimal("0.00")
        )

        payment_methods.append(
            {
                "method": row.payment_method,
                "amount": str(amount),
                "percentage": str(
                    percentage.quantize(
                        Decimal("0.01")
                    )
                ),
            }
        )

    # ---------------------------------------------------------
    # RECENT INVOICES
    # ---------------------------------------------------------

    recent_invoices = db.execute(
        select(Invoice)
        .where(
            Invoice.retailer_id == retailer_id
        )
        .order_by(
            Invoice.created_at.desc()
        )
        .limit(5)
    ).scalars().all()

    recent_invoice_data = [
        {
            "invoice_id": invoice.invoice_id,
            "customer_id": str(invoice.customer_id),
            "invoice_number": invoice.invoice_number,
            "total_amount": str(
                invoice.total_amount
            ),
            "payment_status": invoice.payment_status,
            "status": invoice.status,
            "invoice_date": invoice.invoice_date,
        }
        for invoice in recent_invoices
    ]

    # ---------------------------------------------------------
    # RECENT PAYMENTS
    # ---------------------------------------------------------

    recent_payments = db.execute(
        select(Payment)
        .join(
            Invoice,
            Payment.invoice_id == Invoice.id,
        )
        .where(
            Invoice.retailer_id == retailer_id
        )
        .order_by(
            Payment.created_at.desc()
        )
        .limit(5)
    ).scalars().all()

    recent_payment_data = [
        {
            "payment_id": payment.payment_id,
            "invoice_id": str(
                payment.invoice_id
            ),
            "amount": str(payment.amount),
            "payment_method": payment.payment_method,
            "payment_status": payment.payment_status,
            "paid_at": payment.paid_at,
        }
        for payment in recent_payments
    ]

    # ---------------------------------------------------------
    # LOW STOCK
    # ---------------------------------------------------------

    available_quantity = (
        InventoryItem.quantity_on_hand
        - InventoryItem.quantity_reserved
    )

    low_stock_rows = db.execute(
        select(
            InventoryItem,
            ProductVariant,
        )
        .join(
            ProductVariant,
            InventoryItem.product_variant_id
            == ProductVariant.id,
        )
        .where(
            InventoryItem.retailer_id == retailer_id,
            available_quantity <= InventoryItem.reorder_level,
        )
        .order_by(
            available_quantity.asc()
        )
        .limit(5)
    ).all()

    low_stock_items = [
        {
            "product_variant_id": str(
                variant.id
            ),
            "sku": variant.sku,
            "variant_name": variant.variant_name,
            "quantity_on_hand": item.quantity_on_hand,
            "quantity_reserved": item.quantity_reserved,
            "quantity_available": item.quantity_available,
            "reorder_level": item.reorder_level,
        }
        for item, variant in low_stock_rows
    ]

    # ---------------------------------------------------------
    # RESULT
    # ---------------------------------------------------------

    return {
        "total_customers": total_customers,
        "total_invoices": total_invoices,
        "total_sales": str(total_sales),
        "payments_collected": str(
            payments_collected
        ),
        "outstanding_amount": str(
            outstanding_amount
        ),
        "paid_invoices": paid_invoices,
        "partial_invoices": partial_invoices,
        "unpaid_invoices": unpaid_invoices,
        "sales_overview": sales_overview,
        "payment_methods": payment_methods,
        "recent_invoices": recent_invoice_data,
        "recent_payments": recent_payment_data,
        "low_stock_items": low_stock_items,
    }
