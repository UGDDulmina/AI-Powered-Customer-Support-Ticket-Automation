from fastapi import FastAPI, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.dependencies import get_db
from app.api.customers import router as customers_router

app = FastAPI(
    title="AI Customer Support API",
    description="AI-powered customer support and ticket automation",
    version="1.0.0",
)

app.include_router(
    customers_router,
    prefix="/api/v1",
)


@app.get("/")
def root():
    return {
        "message": "Welcome to AI Customer Support API"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "ai-support-backend"
    }

@app.get("/health/db")
def database_health(
    db: Session = Depends(get_db)
):
    db.execute(text("SELECT 1"))

    return {
        "status": "connected",
        "database": "PostgreSQL"
    }