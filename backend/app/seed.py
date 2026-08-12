from app.core.database import SessionLocal
from app.services.seed_service import seed_authorization_data


def main():
    db = SessionLocal()

    try:
        seed_authorization_data(db)
        print("Authorization data seeded successfully.")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()