import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.database import SessionLocal
from app.services.customer_uploaded_bill_cleanup_service import (
    cleanup_expired_uncertain_bills,
)


def main():
    db = SessionLocal()

    try:
        deleted_count = cleanup_expired_uncertain_bills(db)

        print("Customer uploaded bill cleanup completed.")
        print(f"Expired uncertain bills deleted: {deleted_count}")

    finally:
        db.close()


if __name__ == "__main__":
    main()
