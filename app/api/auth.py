
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.dependencies import get_db
from app.schemas.auth import AgentLoginRequest, TokenResponse
from app.services.auth_service import authenticate_agent
from app.core.security import create_access_token
from app.core.auth_dependencies import get_current_agent
from app.models.support_agent import SupportAgent
from app.schemas.auth import AuthenticatedAgentResponse

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


@router.post(
    "/login",
    response_model=TokenResponse
)
def login(
    payload: AgentLoginRequest,
    db: Session = Depends(get_db)
):
    agent = authenticate_agent(
        db=db,
        email=payload.email,
        password=payload.password
    )

    if agent is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"}
        )

    access_token = create_access_token(
        agent_id=agent.id
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer"
    )

@router.get("/me", response_model=AuthenticatedAgentResponse)
def get_my_profile(
    current_agent: SupportAgent = Depends(get_current_agent),
):
    return current_agent
