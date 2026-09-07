import uuid
from decimal import Decimal

from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.models.customer import Customer
from app.models.invoice import Invoice
from app.models.invoice_item import InvoiceItem
from app.models.payment import Payment
from app.models.product_ownership import ProductOwnership
from app.models.product_transfer import ProductTransfer
from app.models.sales_return import SalesReturn
from app.models.warranty import Warranty


def get_customer_dashboard(
    db: Session,
    customer_id: uuid.UUID,
) -> dict:

    customer = db.execute(
        select(Customer).where(
            Customer.id == customer_id
        )
    ).scalar_one_or_none()

    if customer is None:
        raise ValueError("Customer not found.")

    invoices = list(
        db.execute(
            select(Invoice)
            .where(
                Invoice.customer_id == customer_id,
                Invoice.status == "active",
            )
            .order_by(
                desc(Invoice.invoice_date),
                desc(Invoice.created_at),
            )
        )
        .scalars()
        .all()
    )

    total_invoices = len(invoices)

    total_purchases = sum(
        (
            Decimal(str(invoice.total_amount))
            for invoice in invoices
        ),
        Decimal("0.00"),
    )

    def get_net_paid(invoice_id):
        payments = db.execute(
            select(Payment).where(
                Payment.invoice_id == invoice_id,
            )
        ).scalars().all()

        net_paid = Decimal("0.00")

        for payment in payments:
            if payment.payment_status != "completed":
                continue

            amount = Decimal(str(payment.amount or 0))
            refund = Decimal(str(payment.refund_amount or 0))

            net_paid += max(
                Decimal("0.00"),
                amount - refund,
            )

        return net_paid

    amount_paid = Decimal("0.00")

    refunds_received = Decimal("0.00")

    outstanding_amount = Decimal("0.00")

    invoice_status = {
        "paid": 0,
        "partial": 0,
        "unpaid": 0,
    }

    for invoice in invoices:
        paid = get_net_paid(invoice.id)
        total = Decimal(str(invoice.total_amount))

        amount_paid += paid

        invoice_refund = db.scalar(
            select(
                func.coalesce(
                    func.sum(Payment.refund_amount),
                    0,
                )
            ).where(
                Payment.invoice_id == invoice.id,
                Payment.payment_status == "completed",
                Payment.refund_amount > 0,
            )
        ) or Decimal("0.00")

        refunds_received += Decimal(str(invoice_refund))

        balance = total - paid

        if balance > 0:
            outstanding_amount += balance

        if paid >= total:
            invoice_status["paid"] += 1
        elif paid > 0:
            invoice_status["partial"] += 1
        else:
            invoice_status["unpaid"] += 1

    spending_rows = db.execute(
        select(
            func.date(Invoice.invoice_date).label("date"),
            func.count(Invoice.id).label(
                "invoice_count"
            ),
            func.coalesce(
                func.sum(Invoice.total_amount),
                0,
            ).label("amount"),
        )
        .where(
            Invoice.customer_id == customer_id,
            Invoice.status == "active",
        )
        .group_by(
            func.date(Invoice.invoice_date)
        )
        .order_by(
            func.date(Invoice.invoice_date)
        )
    ).all()

    spending_trend = [
        {
            "date": str(row.date),
            "invoice_count": row.invoice_count,
            "amount": str(row.amount),
        }
        for row in spending_rows
    ]

    recent_invoices = []

    for invoice in invoices[:10]:

        paid = get_net_paid(invoice.id)

        total = Decimal(str(invoice.total_amount))

        if paid >= total:
            payment_status = "paid"
        elif paid > 0:
            payment_status = "partial"
        else:
            payment_status = "unpaid"

        invoice_items = db.execute(
            select(InvoiceItem).where(
                InvoiceItem.invoice_id == invoice.id,
            )
        ).scalars().all()

        item_names = [
            item.product_name
            for item in invoice_items
            if item.product_name
        ]

        recent_invoices.append(
            {
                "id": str(invoice.id),
                "invoice_id": invoice.invoice_id,
                "invoice_number": invoice.invoice_number,
                "item_names": item_names,
                "total_amount": str(invoice.total_amount),
                "payment_status": payment_status,
                "invoice_date": (
                    invoice.invoice_date.isoformat()
                    if invoice.invoice_date
                    else None
                ),
            }
        )

    payment_rows = db.execute(
        select(
            Payment,
            Invoice.id,
            Invoice.invoice_id,
        )
        .join(
            Invoice,
            Invoice.id == Payment.invoice_id,
        )
        .where(
            Invoice.customer_id == customer_id,
            Invoice.status == "active",
            Payment.payment_status == "completed",
        )
        .order_by(
            desc(Payment.paid_at),
            desc(Payment.created_at),
        )
        .limit(10)
    ).all()

    recent_payments = []

    for payment, invoice_db_id, invoice_id in payment_rows:
        payment_items = db.execute(
            select(InvoiceItem).where(
                InvoiceItem.invoice_id == invoice_db_id,
            )
        ).scalars().all()

        item_names = [
            item.product_name
            for item in payment_items
            if item.product_name
        ]

        recent_payments.append(
            {
                "id": str(payment.id),
                "payment_id": payment.payment_id,
                "invoice_id": invoice_id,
                "item_names": item_names,
                "amount": str(payment.amount),
                "payment_status": payment.payment_status,
                "refund_amount": str(
                    payment.refund_amount or Decimal("0.00")
                ),
                "payment_method": payment.payment_method,
                "paid_at": (
                    payment.paid_at.isoformat()
                    if payment.paid_at
                    else None
                ),
            }
        )

    my_products = db.scalar(
        select(func.count(ProductOwnership.id)).where(
            ProductOwnership.customer_id == customer_id,
            ProductOwnership.ownership_status == "active",
        )
    ) or 0

    active_warranties = db.scalar(
        select(func.count(Warranty.id))
        .join(
            Invoice,
            Invoice.id == Warranty.invoice_id,
        )
        .where(
            Warranty.customer_id == customer_id,
            Invoice.customer_id == customer_id,
            Warranty.status == "active",
        )
    ) or 0

    my_returns = db.scalar(
        select(func.count(SalesReturn.id)).where(
            SalesReturn.customer_id == customer_id,
        )
    ) or 0

    product_transfers = db.scalar(
        select(func.count(ProductTransfer.id)).where(
            (
                (ProductTransfer.from_customer_id == customer_id)
                | (ProductTransfer.to_customer_id == customer_id)
            )
        )
    ) or 0

    warranty_rows = db.execute(
        select(Warranty)
        .join(
            Invoice,
            Invoice.id == Warranty.invoice_id,
        )
        .where(
            Warranty.customer_id == customer_id,
            Invoice.customer_id == customer_id,
        )
        .order_by(
            desc(Warranty.created_at)
        )
        .limit(10)
    ).scalars().all()

    warranties = []

    for warranty in warranty_rows:

        product_name = "Product"

        item = db.execute(
            select(InvoiceItem)
            .where(
                InvoiceItem.invoice_id == warranty.invoice_id,
                InvoiceItem.product_variant_id
                == warranty.product_variant_id,
            )
            .limit(1)
        ).scalar_one_or_none()

        if item is not None:
            product_name = item.product_name

        warranties.append(
            {
                "id": str(warranty.id),
                "warranty_id": warranty.warranty_id,
                "invoice_id": str(warranty.invoice_id),
                "product_variant_id": str(
                    warranty.product_variant_id
                ),
                "product_name": product_name,
                "start_date": warranty.start_date.isoformat(),
                "end_date": warranty.end_date.isoformat(),
                "duration_months": warranty.duration_months,
                "is_transferable": warranty.is_transferable,
                "status": warranty.status,
            }
        )

    return {
        "customer": {
            "id": str(customer.id),
            "customer_id": customer.customer_id,
            "full_name": customer.full_name,
            "phone_number": customer.phone_number,
            "email": customer.email,
            "status": customer.status,
        },
        "total_purchases": str(total_purchases),
        "total_invoices": total_invoices,
        "amount_paid": str(amount_paid),
        "refunds_received": str(refunds_received),
        "outstanding_amount": str(outstanding_amount),
        "invoice_status": invoice_status,
        "spending_trend": spending_trend,
        "recent_invoices": recent_invoices,
        "recent_payments": recent_payments,
        "warranties": warranties,
        "my_products": my_products,
        "active_warranties": active_warranties,
        "my_returns": my_returns,
        "product_transfers": product_transfers,
    }
