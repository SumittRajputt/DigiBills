import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.database import SessionLocal
from app.services.subscription_service import (
    process_subscription_lifecycle,
)


def main():
    db = SessionLocal()

    try:
        result = process_subscription_lifecycle(db)

        print("Subscription lifecycle processed.")
        print(result)

    finally:
        db.close()


if __name__ == "__main__":
    main()
