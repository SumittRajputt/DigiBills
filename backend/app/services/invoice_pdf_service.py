from decimal import Decimal
from io import BytesIO
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


# =========================================================
# HELPERS
# =========================================================

def money(value):
    amount = Decimal(str(value or 0))
    return f"Rs. {amount:,.2f}"


def safe_text(value, fallback="—"):
    if value is None:
        return fallback

    value = str(value).strip()

    if not value:
        return fallback

    return escape(value)


# =========================================================
# PDF GENERATOR
# =========================================================

def generate_invoice_pdf(
    invoice,
    customer,
    retailer,
    items,
    payment_summary,
):
    buffer = BytesIO()

    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=13 * mm,
        leftMargin=13 * mm,
        topMargin=12 * mm,
        bottomMargin=12 * mm,
        title=f"Invoice {invoice.invoice_id}",
        author="DigiBills",
    )

    styles = getSampleStyleSheet()

    # =====================================================
    # COLORS
    # =====================================================

    navy = colors.HexColor("#0f172a")
    blue = colors.HexColor("#2563eb")
    slate = colors.HexColor("#64748b")
    light_slate = colors.HexColor("#f8fafc")
    border = colors.HexColor("#dbe3ec")
    soft_border = colors.HexColor("#e5e7eb")
    green = colors.HexColor("#15803d")
    amber = colors.HexColor("#b45309")
    red = colors.HexColor("#b91c1c")

    # =====================================================
    # STYLES
    # =====================================================

    title_style = ParagraphStyle(
        "InvoiceTitle",
        parent=styles["Title"],
        fontName="Helvetica",
        fontSize=23,
        leading=26,
        textColor=navy,
        alignment=TA_LEFT,
        spaceAfter=2,
    )

    invoice_label_style = ParagraphStyle(
        "InvoiceLabel",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=10,
        textColor=slate,
        alignment=TA_RIGHT,
    )

    invoice_number_style = ParagraphStyle(
        "InvoiceNumber",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=12,
        leading=15,
        textColor=navy,
        alignment=TA_RIGHT,
    )

    business_style = ParagraphStyle(
        "Business",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        textColor=navy,
    )

    section_style = ParagraphStyle(
        "Section",
        parent=styles["Heading3"],
        fontName="Helvetica",
        fontSize=11,
        leading=14,
        textColor=navy,
        spaceAfter=6,
    )

    normal_style = ParagraphStyle(
        "InvoiceNormal",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=12,
        textColor=navy,
    )

    small_style = ParagraphStyle(
        "Small",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=7.5,
        leading=10,
        textColor=slate,
    )

    right_style = ParagraphStyle(
        "Right",
        parent=normal_style,
        alignment=TA_RIGHT,
    )

    center_style = ParagraphStyle(
        "Center",
        parent=normal_style,
        alignment=TA_CENTER,
    )

    header_style = ParagraphStyle(
        "TableHeader",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=7.5,
        leading=9,
        textColor=colors.white,
        alignment=TA_LEFT,
    )

    header_right_style = ParagraphStyle(
        "TableHeaderRight",
        parent=header_style,
        alignment=TA_RIGHT,
    )

    header_center_style = ParagraphStyle(
        "TableHeaderCenter",
        parent=header_style,
        alignment=TA_CENTER,
    )

    total_label_style = ParagraphStyle(
        "TotalLabel",
        parent=normal_style,
        fontSize=9,
        leading=12,
    )

    total_value_style = ParagraphStyle(
        "TotalValue",
        parent=right_style,
        fontSize=11,
        leading=14,
    )

    story = []

    # =====================================================
    # DATA
    # =====================================================

    business_name = safe_text(
        getattr(retailer, "business_name", None),
        "DigiBills Retailer",
    )

    retailer_address = safe_text(
        getattr(retailer, "address", None)
    )

    retailer_phone = safe_text(
        getattr(retailer, "phone_number", None)
    )

    retailer_email = safe_text(
        getattr(retailer, "email", None)
    )

    customer_name = safe_text(
        getattr(customer, "full_name", None)
    )

    customer_id = safe_text(
        getattr(customer, "customer_id", None)
    )

    customer_phone = safe_text(
        getattr(customer, "phone_number", None)
    )

    customer_email = safe_text(
        getattr(customer, "email", None)
    )

    invoice_number = safe_text(
        invoice.invoice_number
        or invoice.invoice_id
    )

    invoice_id = safe_text(invoice.invoice_id)

    invoice_date = (
        invoice.invoice_date.strftime("%d %b %Y")
        if invoice.invoice_date
        else "—"
    )

    net_paid = Decimal(
        str(payment_summary.get("net_paid", 0) or 0)
    )

    outstanding = Decimal(
        str(payment_summary.get("outstanding", 0) or 0)
    )

    payment_status = str(
        payment_summary.get(
            "payment_status",
            invoice.payment_status or "unpaid",
        )
    ).upper()

    # =====================================================
    # HEADER
    # =====================================================

    header_left = [
        Paragraph(
            business_name,
            title_style,
        ),
        Spacer(1, 2),
        Paragraph(
            "Digital billing & invoice management",
            small_style,
        ),
    ]

    header_right = [
        Paragraph(
            "TAX INVOICE",
            ParagraphStyle(
                "TaxInvoice",
                parent=invoice_number_style,
                fontSize=18,
                leading=21,
                textColor=blue,
            ),
        ),
        Spacer(1, 2),
        Paragraph(
            f"Invoice No. {invoice_number}",
            invoice_label_style,
        ),
        Paragraph(
            f"Date: {safe_text(invoice_date)}",
            invoice_label_style,
        ),
    ]

    header_table = Table(
        [
            [
                header_left,
                header_right,
            ]
        ],
        colWidths=[
            112 * mm,
            68 * mm,
        ],
    )

    header_table.setStyle(
        TableStyle(
            [
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "TOP",
                ),
                (
                    "ALIGN",
                    (1, 0),
                    (1, 0),
                    "RIGHT",
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    0,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    0,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    0,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    0,
                ),
            ]
        )
    )

    story.append(header_table)
    story.append(Spacer(1, 5))

    # Accent line
    accent_table = Table(
        [[""]],
        colWidths=[180 * mm],
        rowHeights=[1.5 * mm],
    )

    accent_table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, -1),
                    blue,
                ),
                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    0,
                    blue,
                ),
            ]
        )
    )

    story.append(accent_table)
    story.append(Spacer(1, 10))

    # =====================================================
    # INFORMATION CARDS
    # =====================================================

    business_block = (
        "<b>FROM</b><br/>"
        f"<font size='11'><b>{business_name}</b></font><br/>"
        f"{retailer_address}<br/>"
        f"Phone: {retailer_phone}<br/>"
        f"Email: {retailer_email}"
    )

    customer_block = (
        "<b>BILL TO</b><br/>"
        f"<font size='11'><b>{customer_name}</b></font><br/>"
        f"Customer ID: {customer_id}<br/>"
        f"Phone: {customer_phone}<br/>"
        f"Email: {customer_email}"
    )

    invoice_block = (
        "<b>INVOICE DETAILS</b><br/>"
        f"Invoice ID: {invoice_id}<br/>"
        f"Invoice No: {invoice_number}<br/>"
        f"Invoice Date: {safe_text(invoice_date)}"
    )

    info_table = Table(
        [
            [
                Paragraph(business_block, normal_style),
                Paragraph(customer_block, normal_style),
                Paragraph(invoice_block, normal_style),
            ]
        ],
        colWidths=[
            60 * mm,
            60 * mm,
            60 * mm,
        ],
    )

    info_table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, -1),
                    light_slate,
                ),
                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    0.6,
                    border,
                ),
                (
                    "INNERGRID",
                    (0, 0),
                    (-1, -1),
                    0.4,
                    soft_border,
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "TOP",
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    9,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    9,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    9,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    9,
                ),
            ]
        )
    )

    story.append(info_table)
    story.append(Spacer(1, 14))

    # =====================================================
    # ITEMS
    # =====================================================

    story.append(
        Paragraph(
            "Items",
            section_style,
        )
    )

    item_rows = [
        [
            Paragraph("#", header_center_style),
            Paragraph("Product", header_style),
            Paragraph("SKU", header_style),
            Paragraph("Qty", header_center_style),
            Paragraph("Unit Price", header_right_style),
            Paragraph("Tax", header_right_style),
            Paragraph("Amount", header_right_style),
        ]
    ]

    if items:
        for index, item in enumerate(items, start=1):
            tax_text = (
                f"{money(item.tax_amount)}"
                f"<br/><font size='7'>"
                f"{safe_text(item.tax_rate)}%"
                f"</font>"
            )

            item_rows.append(
                [
                    Paragraph(
                        str(index),
                        center_style,
                    ),
                    Paragraph(
                        safe_text(
                            item.product_name
                        ),
                        normal_style,
                    ),
                    Paragraph(
                        safe_text(item.sku),
                        small_style,
                    ),
                    Paragraph(
                        str(item.quantity),
                        center_style,
                    ),
                    Paragraph(
                        money(item.unit_price),
                        right_style,
                    ),
                    Paragraph(
                        tax_text,
                        right_style,
                    ),
                    Paragraph(
                        f"<b>{money(item.line_total)}</b>",
                        right_style,
                    ),
                ]
            )
    else:
        item_rows.append(
            [
                Paragraph(
                    "—",
                    center_style,
                ),
                Paragraph(
                    "No invoice items",
                    normal_style,
                ),
                Paragraph(
                    "—",
                    small_style,
                ),
                Paragraph(
                    "—",
                    center_style,
                ),
                Paragraph(
                    "—",
                    right_style,
                ),
                Paragraph(
                    "—",
                    right_style,
                ),
                Paragraph(
                    "—",
                    right_style,
                ),
            ]
        )

    items_table = Table(
        item_rows,
        colWidths=[
            9 * mm,
            53 * mm,
            27 * mm,
            13 * mm,
            27 * mm,
            25 * mm,
            26 * mm,
        ],
        repeatRows=1,
    )

    items_table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    navy,
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.4,
                    border,
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE",
                ),
                (
                    "ROWBACKGROUNDS",
                    (0, 1),
                    (-1, -1),
                    [
                        colors.white,
                        colors.HexColor("#f8fafc"),
                    ],
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    6,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    6,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    7,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    7,
                ),
            ]
        )
    )

    story.append(items_table)
    story.append(Spacer(1, 12))

    # =====================================================
    # TOTALS + PAYMENT STATUS
    # =====================================================

    summary_rows = [
        [
            Paragraph("Subtotal", normal_style),
            Paragraph(
                money(invoice.subtotal),
                right_style,
            ),
        ],
        [
            Paragraph("Discount", normal_style),
            Paragraph(
                money(invoice.discount_amount),
                right_style,
            ),
        ],
        [
            Paragraph("Tax", normal_style),
            Paragraph(
                money(invoice.tax_amount),
                right_style,
            ),
        ],
        [
            Paragraph(
                "<b>Grand Total</b>",
                total_label_style,
            ),
            Paragraph(
                f"<b>{money(invoice.total_amount)}</b>",
                total_value_style,
            ),
        ],
        [
            Paragraph("Paid", normal_style),
            Paragraph(
                money(net_paid),
                right_style,
            ),
        ],
        [
            Paragraph(
                "<b>Outstanding</b>",
                normal_style,
            ),
            Paragraph(
                f"<b>{money(outstanding)}</b>",
                right_style,
            ),
        ],
        [
            Paragraph(
                "<b>Payment Status</b>",
                normal_style,
            ),
            Paragraph(
                f"<b>{payment_status}</b>",
                right_style,
            ),
        ],
    ]

    summary_table = Table(
        summary_rows,
        colWidths=[
            58 * mm,
            55 * mm,
        ],
    )

    status_background = light_slate

    if payment_status == "PAID":
        status_background = colors.HexColor("#ecfdf5")
    elif payment_status == "PARTIAL":
        status_background = colors.HexColor("#fffbeb")
    elif payment_status == "UNPAID":
        status_background = colors.HexColor("#fef2f2")

    summary_table.setStyle(
        TableStyle(
            [
                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    0.7,
                    border,
                ),
                (
                    "INNERGRID",
                    (0, 0),
                    (-1, -1),
                    0.3,
                    soft_border,
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    9,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    9,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    7,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    7,
                ),
                (
                    "BACKGROUND",
                    (0, 3),
                    (-1, 3),
                    colors.HexColor("#eff6ff"),
                ),
                (
                    "BACKGROUND",
                    (0, 6),
                    (-1, 6),
                    status_background,
                ),
            ]
        )
    )

    payment_label = (
        "PAID IN FULL"
        if payment_status == "PAID"
        else (
            "PARTIALLY PAID"
            if payment_status == "PARTIAL"
            else "PAYMENT DUE"
        )
    )

    payment_color = (
        green
        if payment_status == "PAID"
        else (
            amber
            if payment_status == "PARTIAL"
            else red
        )
    )

    payment_box = Table(
        [
            [
                Paragraph(
                    "PAYMENT SUMMARY",
                    ParagraphStyle(
                        "PaymentHeading",
                        parent=section_style,
                        fontSize=10,
                        textColor=navy,
                        spaceAfter=3,
                    ),
                )
            ],
            [
                Paragraph(
                    payment_label,
                    ParagraphStyle(
                        "PaymentStatus",
                        parent=styles["Normal"],
                        fontName="Helvetica",
                        fontSize=13,
                        leading=16,
                        textColor=payment_color,
                        alignment=TA_LEFT,
                    ),
                )
            ],
            [
                Paragraph(
                    f"Paid: <b>{money(net_paid)}</b>",
                    normal_style,
                )
            ],
            [
                Paragraph(
                    f"Balance Due: <b>{money(outstanding)}</b>",
                    normal_style,
                )
            ],
        ],
        colWidths=[58 * mm],
    )

    payment_box.setStyle(
        TableStyle(
            [
                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    0.7,
                    border,
                ),
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, -1),
                    light_slate,
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    9,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    9,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    7,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    7,
                ),
            ]
        )
    )

    totals_wrapper = Table(
        [
            [
                payment_box,
                summary_table,
            ]
        ],
        colWidths=[
            62 * mm,
            118 * mm,
        ],
    )

    totals_wrapper.setStyle(
        TableStyle(
            [
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "TOP",
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    0,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    0,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    0,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    0,
                ),
            ]
        )
    )

    story.append(totals_wrapper)
    story.append(Spacer(1, 14))

    # =====================================================
    # NOTES
    # =====================================================

    if invoice.notes:
        notes_table = Table(
            [
                [
                    Paragraph(
                        "<b>Notes</b>",
                        section_style,
                    )
                ],
                [
                    Paragraph(
                        safe_text(invoice.notes),
                        normal_style,
                    )
                ],
            ],
            colWidths=[180 * mm],
        )

        notes_table.setStyle(
            TableStyle(
                [
                    (
                        "BOX",
                        (0, 0),
                        (-1, -1),
                        0.6,
                        border,
                    ),
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, 0),
                        light_slate,
                    ),
                    (
                        "LEFTPADDING",
                        (0, 0),
                        (-1, -1),
                        9,
                    ),
                    (
                        "RIGHTPADDING",
                        (0, 0),
                        (-1, -1),
                        9,
                    ),
                    (
                        "TOPPADDING",
                        (0, 0),
                        (-1, -1),
                        7,
                    ),
                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, -1),
                        7,
                    ),
                ]
            )
        )

        story.append(notes_table)
        story.append(Spacer(1, 12))

    # =====================================================
    # FOOTER
    # =====================================================

    footer_table = Table(
        [
            [
                Paragraph(
                    "<b>Thank you for your business!</b>",
                    ParagraphStyle(
                        "ThankYou",
                        parent=normal_style,
                        fontSize=9,
                        textColor=navy,
                    ),
                ),
                Paragraph(
                    "Generated electronically by DigiBills",
                    ParagraphStyle(
                        "FooterRight",
                        parent=small_style,
                        alignment=TA_RIGHT,
                    ),
                ),
            ]
        ],
        colWidths=[
            90 * mm,
            90 * mm,
        ],
    )

    footer_table.setStyle(
        TableStyle(
            [
                (
                    "LINEABOVE",
                    (0, 0),
                    (-1, 0),
                    0.5,
                    border,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    8,
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    0,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    0,
                ),
            ]
        )
    )

    story.append(footer_table)

    # =====================================================
    # BUILD
    # =====================================================

    document.build(story)

    buffer.seek(0)

    return buffer
