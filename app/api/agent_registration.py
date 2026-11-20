from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.dependencies import get_db
from app.models.support_agent import SupportAgent
from app.schemas.agent_registration import (
    AgentRegistrationRequest,
    AgentRegistrationResponse,
)
from app.core.security import hash_password
from app.core.auth_dependencies import require_admin

router = APIRouter(
    prefix="/agents",
    tags=["Agent Registration"],
)


@router.post(
    "/register",
    response_model=AgentRegistrationResponse,
    status_code=status.HTTP_201_CREATED,
)
def register_agent(
    payload: AgentRegistrationRequest,
    db: Session = Depends(get_db),
    admin: SupportAgent = Depends(require_admin),
):
    email = str(payload.email).strip().lower()

    existing_agent = db.scalar(
        select(SupportAgent).where(SupportAgent.email == email)
    )

    if existing_agent:
        raise HTTPException(
            status_code=409,
            detail="Agent email already exists",
        )

    agent = SupportAgent(
        name=payload.name.strip(),
        email=email,
        password_hash=hash_password(payload.password),
        role=payload.role,
        is_active=True,
    )

    db.add(agent)

    try:
        db.commit()
        db.refresh(agent)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Agent email already exists",
        )

    return agent