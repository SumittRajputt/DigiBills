from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CUSTOMER_BILL_DIR = PROJECT_ROOT / "uploads" / "customer-bills"

# Keep this configurable later if you want a different limit.
MAX_UPLOAD_SIZE = 10 * 1024 * 1024

ALLOWED_CONTENT_TYPE = "application/pdf"
PDF_MAGIC_BYTES = b"%PDF-"


async def save_customer_bill(
    upload_file: UploadFile,
    bill_id: str,
) -> tuple[str, int]:
    """
    Validate and securely store a customer-uploaded PDF bill.

    Returns:
        tuple[str, int]: storage path and file size.
    """

    if upload_file.content_type != ALLOWED_CONTENT_TYPE:
        raise ValueError(
            "Only PDF files are allowed."
        )

    contents = await upload_file.read()

    if not contents:
        raise ValueError(
            "The uploaded PDF is empty."
        )

    if len(contents) > MAX_UPLOAD_SIZE:
        raise ValueError(
            "The uploaded PDF must be 10 MB or smaller."
        )

    if not contents.startswith(PDF_MAGIC_BYTES):
        raise ValueError(
            "The uploaded file is not a valid PDF."
        )

    CUSTOMER_BILL_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    filename = f"{bill_id}_{uuid4().hex}.pdf"
    destination = CUSTOMER_BILL_DIR / filename

    destination.write_bytes(contents)

    return (
        str(destination.relative_to(PROJECT_ROOT)),
        len(contents),
    )
