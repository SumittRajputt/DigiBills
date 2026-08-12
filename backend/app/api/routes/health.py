from fastapi import APIRouter
from sqlalchemy import text

from app.core.database import engine


router = APIRouter(
    prefix="/health",
    tags=["Health"],
)


@router.get("")
def health_check():
    return {
        "status": "healthy",
        "service": "DigiBills API",
    }


@router.get("/database")
def database_health_check():
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1")).scalar()

    return {
        "status": "healthy",
        "database": "connected",
        "result": result,
    }