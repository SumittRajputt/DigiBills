from pathlib import Path
import shutil
import subprocess
import tempfile
from typing import List

from pypdf import PdfReader


PROJECT_ROOT = Path(__file__).resolve().parents[2]

TESSERACT_COMMAND = "tesseract"
PDFTOPPM_COMMAND = "pdftoppm"


class CustomerBillPdfExtractionError(Exception):
    """Raised when a customer bill PDF cannot be read."""


def normalize_pdf_text(text: str) -> str:
    """
    Normalize extracted PDF text without changing its meaning.
    """

    if not text:
        return ""

    lines = []

    for line in text.splitlines():
        cleaned = " ".join(line.split())

        if cleaned:
            lines.append(cleaned)

    return "\n".join(lines)


def _extract_text_with_pypdf(
    pdf_path: Path,
) -> tuple[str, int]:
    """
    Extract text from a text-based PDF using pypdf.
    """

    try:
        reader = PdfReader(str(pdf_path))
    except Exception as exc:
        raise CustomerBillPdfExtractionError(
            "Customer bill PDF could not be opened."
        ) from exc

    page_text: List[str] = []

    for page_number, page in enumerate(
        reader.pages,
        start=1,
    ):
        try:
            text = page.extract_text() or ""
        except Exception as exc:
            raise CustomerBillPdfExtractionError(
                f"Could not extract text from PDF page {page_number}."
            ) from exc

        normalized = normalize_pdf_text(text)

        if normalized:
            page_text.append(
                f"[Page {page_number}]\n{normalized}"
            )

    return (
        "\n\n".join(page_text),
        len(reader.pages),
    )


def _run_ocr(
    pdf_path: Path,
) -> tuple[str, int]:
    """
    Render PDF pages with Poppler and extract text with Tesseract.
    """

    if shutil.which(PDFTOPPM_COMMAND) is None:
        raise CustomerBillPdfExtractionError(
            "PDF OCR is unavailable because pdftoppm is not installed."
        )

    if shutil.which(TESSERACT_COMMAND) is None:
        raise CustomerBillPdfExtractionError(
            "PDF OCR is unavailable because tesseract is not installed."
        )

    try:
        reader = PdfReader(str(pdf_path))
        page_count = len(reader.pages)
    except Exception as exc:
        raise CustomerBillPdfExtractionError(
            "Could not determine the number of PDF pages for OCR."
        ) from exc

    if page_count == 0:
        raise CustomerBillPdfExtractionError(
            "The customer bill PDF contains no pages."
        )

    ocr_pages: List[str] = []

    with tempfile.TemporaryDirectory(
        prefix="digibills_ocr_"
    ) as temp_dir:

        output_prefix = Path(temp_dir) / "page"

        render_result = subprocess.run(
            [
                PDFTOPPM_COMMAND,
                "-jpeg",
                "-r",
                "200",
                str(pdf_path),
                str(output_prefix),
            ],
            capture_output=True,
            text=True,
        )

        if render_result.returncode != 0:
            raise CustomerBillPdfExtractionError(
                "Could not render the PDF pages for OCR."
            )

        image_paths = sorted(
            Path(temp_dir).glob("page-*.jpg")
        )

        if not image_paths:
            raise CustomerBillPdfExtractionError(
                "No PDF pages were rendered for OCR."
            )

        for page_number, image_path in enumerate(
            image_paths,
            start=1,
        ):
            ocr_result = subprocess.run(
                [
                    TESSERACT_COMMAND,
                    str(image_path),
                    "stdout",
                    "--psm",
                    "6",
                ],
                capture_output=True,
                text=True,
            )

            if ocr_result.returncode != 0:
                raise CustomerBillPdfExtractionError(
                    f"OCR failed on PDF page {page_number}."
                )

            text = normalize_pdf_text(
                ocr_result.stdout
            )

            if text:
                ocr_pages.append(
                    f"[Page {page_number}]\n{text}"
                )

    return (
        "\n\n".join(ocr_pages),
        page_count,
    )


def extract_pdf_text(
    storage_path: str,
) -> tuple[str, int, str]:
    """
    Extract text from a customer-uploaded PDF.

    Extraction order:

    1. pypdf for text-based PDFs.
    2. Tesseract OCR fallback for scanned PDFs.

    Returns:
        tuple[str, int, str]:
            normalized text,
            page count,
            extraction engine.
    """

    pdf_path = PROJECT_ROOT / storage_path

    if not pdf_path.exists():
        raise CustomerBillPdfExtractionError(
            "Customer bill PDF could not be found."
        )

    if not pdf_path.is_file():
        raise CustomerBillPdfExtractionError(
            "Customer bill storage path is not a file."
        )

    text, page_count = _extract_text_with_pypdf(
        pdf_path
    )

    if text.strip():
        return text, page_count, "pypdf"

    ocr_text, ocr_page_count = _run_ocr(
        pdf_path
    )

    return (
        ocr_text,
        ocr_page_count,
        "tesseract_ocr",
    )
