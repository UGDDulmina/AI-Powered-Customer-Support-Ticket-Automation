from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status
)

from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.dependencies import get_db

from app.schemas.auth import (
    AgentLoginRequest,
    TokenResponse,
    AuthenticatedAgentResponse,
    AgentProfileUpdateRequest,
    AgentChangePasswordRequest,
    PasswordChangeResponse
)

from app.services.auth_service import authenticate_agent

from app.core.security import (
    create_access_token,
    hash_password,
    verify_password
)

from app.core.auth_dependencies import get_current_agent
from app.models.support_agent import SupportAgent


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


@router.get(
    "/me",
    response_model=AuthenticatedAgentResponse
)
def get_my_profile(
    current_agent: SupportAgent = Depends(
        get_current_agent
    )
):
    return current_agent


@router.patch(
    "/me",
    response_model=AuthenticatedAgentResponse
)
def update_my_profile(
    payload: AgentProfileUpdateRequest,
    db: Session = Depends(get_db),
    current_agent: SupportAgent = Depends(
        get_current_agent
    )
):
    normalized_email = payload.email.strip().lower()

    email_changed = (
        normalized_email != current_agent.email
    )

    if email_changed:
        if not payload.current_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is required to change email"
            )

        if (
            not current_agent.password_hash
            or not verify_password(
                payload.current_password,
                current_agent.password_hash
            )
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )

        existing_agent = db.scalar(
            select(SupportAgent).where(
                func.lower(SupportAgent.email)
                == normalized_email,
                SupportAgent.id != current_agent.id
            )
        )

        if existing_agent is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email address is already in use"
            )

    current_agent.name = payload.name
    current_agent.email = normalized_email

    try:
        db.commit()
        db.refresh(current_agent)

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Unable to update profile. Email may already be in use"
        )

    return current_agent


@router.patch(
    "/change-password",
    response_model=PasswordChangeResponse
)
def change_my_password(
    payload: AgentChangePasswordRequest,
    db: Session = Depends(get_db),
    current_agent: SupportAgent = Depends(
        get_current_agent
    )
):
    if not current_agent.password_hash:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account password is not configured"
        )

    if not verify_password(
        payload.current_password,
        current_agent.password_hash
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )

    if verify_password(
        payload.new_password,
        current_agent.password_hash
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must differ from current password"
        )

    current_agent.password_hash = hash_password(
        payload.new_password
    )

    db.commit()

    return PasswordChangeResponse(
        message="Password changed successfully"
    )