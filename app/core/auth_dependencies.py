from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.db.dependencies import get_db
from app.models.support_agent import SupportAgent
from app.core.security import decode_access_token

bearer_scheme = HTTPBearer()


def get_current_agent(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> SupportAgent:

    agent_id = decode_access_token(credentials.credentials)

    if agent_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token",
        )

    agent = db.get(SupportAgent, agent_id)

    if agent is None or not agent.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Agent not found or inactive",
        )

    return agent


def require_admin(
    current_agent: SupportAgent = Depends(get_current_agent),
) -> SupportAgent:

    if current_agent.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )

    return current_agent