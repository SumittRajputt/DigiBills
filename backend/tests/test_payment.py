
from decimal import Decimal
from uuid import uuid4

from app.models.customer import Customer
from app.models.invoice import Invoice
from app.models.payment import Payment
from app.models.retailer import Retailer
from app.models.user import User
from app.services.payment_service import (
    cancel_payment,
    create_payment,
    refund_payment,
)


def create_payment_context(db, total_amount=Decimal("10000.00")):
    user = User(
        phone_number=f"999{uuid4().hex[:7]}",
        status="active",
    )
    db.add(user)
    db.flush()

    retailer = Retailer(
        retailer_id=f"RET-PAY-{uuid4().hex[:8].upper()}",
        owner_user_id=user.id,
        business_name="Payment Test Retailer",
        phone_number=user.phone_number,
        status="active",
    )
    db.add(retailer)
    db.flush()

    customer_user = User(
        phone_number=f"888{uuid4().hex[:7]}",
        status="active",
    )
    db.add(customer_user)
    db.flush()

    customer = Customer(
        customer_id=f"CUS-PAY-{uuid4().hex[:8].upper()}",
        user_id=customer_user.id,
        full_name="Payment Test Customer",
        phone_number=customer_user.phone_number,
        status="active",
    )
    db.add(customer)
    db.flush()

    invoice = Invoice(
        invoice_id=f"INV-PAY-{uuid4().hex[:10].upper()}",
        retailer_id=retailer.id,
        customer_id=customer.id,
        invoice_date=__import__("datetime").datetime.utcnow(),
        subtotal=total_amount,
        discount_amount=Decimal("0.00"),
        tax_amount=Decimal("0.00"),
        total_amount=total_amount,
        payment_status="unpaid",
        status="active",
    )
    db.add(invoice)
    db.flush()

    return user, retailer, customer, invoice


def test_create_payment_marks_invoice_partial(db):
    user, retailer, customer, invoice = create_payment_context(db)

    payment = create_payment(
        db=db,
        invoice=invoice,
        amount=Decimal("4000.00"),
        payment_method=" CASH ",
        retailer_id=retailer.id,
        user_id=user.id,
    )

    assert payment.payment_status == "completed"
    assert payment.payment_method == "cash"
    assert payment.amount == Decimal("4000.00")
    assert invoice.payment_status == "partial"


def test_create_payment_marks_invoice_paid(db):
    user, retailer, customer, invoice = create_payment_context(db)

    payment = create_payment(
        db=db,
        invoice=invoice,
        amount=Decimal("10000.00"),
        payment_method="UPI",
        retailer_id=retailer.id,
        user_id=user.id,
    )

    assert payment.payment_status == "completed"
    assert invoice.payment_status == "paid"


def test_payment_cannot_exceed_remaining_amount(db):
    user, retailer, customer, invoice = create_payment_context(db)

    create_payment(
        db=db,
        invoice=invoice,
        amount=Decimal("7000.00"),
        payment_method="cash",
        retailer_id=retailer.id,
        user_id=user.id,
    )

    try:
        create_payment(
            db=db,
            invoice=invoice,
            amount=Decimal("4000.00"),
            payment_method="cash",
            retailer_id=retailer.id,
            user_id=user.id,
        )
        assert False, "Expected ValueError"
    except ValueError as exc:
        assert "cannot exceed" in str(exc)


def test_fully_paid_invoice_rejects_additional_payment(db):
    user, retailer, customer, invoice = create_payment_context(db)

    create_payment(
        db=db,
        invoice=invoice,
        amount=Decimal("10000.00"),
        payment_method="cash",
        retailer_id=retailer.id,
        user_id=user.id,
    )

    try:
        create_payment(
            db=db,
            invoice=invoice,
            amount=Decimal("1.00"),
            payment_method="cash",
            retailer_id=retailer.id,
            user_id=user.id,
        )
        assert False, "Expected ValueError"
    except ValueError as exc:
        assert "fully paid" in str(exc)


def test_partial_refund_changes_invoice_to_partial(db):
    user, retailer, customer, invoice = create_payment_context(db)

    payment = create_payment(
        db=db,
        invoice=invoice,
        amount=Decimal("10000.00"),
        payment_method="cash",
        retailer_id=retailer.id,
        user_id=user.id,
    )

    payment = refund_payment(
        db=db,
        payment=payment,
        refund_amount=Decimal("3000.00"),
        retailer_id=retailer.id,
        user_id=user.id,
    )

    assert payment.refund_amount == Decimal("3000.00")
    assert payment.refund_status == "partial"
    assert invoice.payment_status == "partial"


def test_full_refund_marks_invoice_unpaid(db):
    user, retailer, customer, invoice = create_payment_context(db)

    payment = create_payment(
        db=db,
        invoice=invoice,
        amount=Decimal("10000.00"),
        payment_method="cash",
        retailer_id=retailer.id,
        user_id=user.id,
    )

    payment = refund_payment(
        db=db,
        payment=payment,
        refund_amount=Decimal("10000.00"),
        retailer_id=retailer.id,
        user_id=user.id,
    )

    assert payment.refund_amount == Decimal("10000.00")
    assert payment.refund_status == "refunded"
    assert invoice.payment_status == "unpaid"


def test_refund_cannot_exceed_payment_amount(db):
    user, retailer, customer, invoice = create_payment_context(db)

    payment = create_payment(
        db=db,
        invoice=invoice,
        amount=Decimal("5000.00"),
        payment_method="cash",
        retailer_id=retailer.id,
        user_id=user.id,
    )

    try:
        refund_payment(
            db=db,
            payment=payment,
            refund_amount=Decimal("5000.01"),
            retailer_id=retailer.id,
            user_id=user.id,
        )
        assert False, "Expected ValueError"
    except ValueError as exc:
        assert "cannot exceed" in str(exc)


def test_cancel_payment_changes_invoice_status(db):
    user, retailer, customer, invoice = create_payment_context(db)

    payment = create_payment(
        db=db,
        invoice=invoice,
        amount=Decimal("4000.00"),
        payment_method="cash",
        retailer_id=retailer.id,
        user_id=user.id,
    )

    payment = cancel_payment(
        db=db,
        payment=payment,
        retailer_id=retailer.id,
        user_id=user.id,
    )

    assert payment.payment_status == "cancelled"
    assert invoice.payment_status == "unpaid"


def test_refunded_payment_cannot_be_cancelled(db):
    user, retailer, customer, invoice = create_payment_context(db)

    payment = create_payment(
        db=db,
        invoice=invoice,
        amount=Decimal("5000.00"),
        payment_method="cash",
        retailer_id=retailer.id,
        user_id=user.id,
    )

    refund_payment(
        db=db,
        payment=payment,
        refund_amount=Decimal("1000.00"),
        retailer_id=retailer.id,
        user_id=user.id,
    )

    try:
        cancel_payment(
            db=db,
            payment=payment,
            retailer_id=retailer.id,
            user_id=user.id,
        )
        assert False, "Expected ValueError"
    except ValueError as exc:
        assert "refunds cannot be cancelled" in str(exc)
