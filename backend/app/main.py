from fastapi import FastAPI

from app.api.router import api_router


app = FastAPI(
    title="DigiBills API",
    description="Retail billing, inventory, analytics, and business management platform.",
    version="1.0.0",
)


app.include_router(api_router)