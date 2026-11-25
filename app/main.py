from fastapi import FastAPI, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.dependencies import get_db
from app.api.customers import router as customers_router
from app.api.tickets import router as tickets_router
from app.api.ticketMessage import router as ticketMessage_router
from app.api.stats import router as status_router
from app.api.ai_suggestions import router as ai_suggestions_router
from app.api.ai_automation import router as ai_automation_router
from app.api.support_agent import router as support_agent      
from app.api.ai_analytics import router as ai_analytics_router
from app.api.auth import router as auth_router
from app.api.agent_registration import router as agent_registration_router
import os
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="AI Customer Support API",
    description="AI-powered customer support and ticket automation",
    version="1.0.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:4173",
        "http://127.0.0.1:4173",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(
    customers_router,
    prefix="/api/v1"
)

app.include_router(
    tickets_router,
    prefix="/api/v1"
)

app.include_router(
    ticketMessage_router,
    prefix="/api/v1"
)

app.include_router(
    status_router,
    prefix="/api/v1"
)

app.include_router(
    ai_suggestions_router,
    prefix="/api/v1"
)

app.include_router(
    ai_automation_router,
    prefix="/api/v1"
)

app.include_router(
    support_agent,
    prefix="/api/v1"
)

app.include_router(
    ai_analytics_router, 
    prefix="/api/v1"
)

app.include_router(
    auth_router,
    prefix="/api/v1"
)

app.include_router(
    agent_registration_router,
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