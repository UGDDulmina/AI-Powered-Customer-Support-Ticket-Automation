
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.support_agent import SupportAgent
from app.core.security import verify_password


def authenticate_agent(
    db: Session,
    email: str,
    password: str
) -> SupportAgent | None:

    normalized_email = email.strip().lower()

    agent = db.scalar(
        select(SupportAgent).where(
            SupportAgent.email == normalized_email
        )
    )

    if agent is None:
        return None

    if not agent.is_active:
        return None

    if not agent.password_hash:
        return None

    if not verify_password(password, agent.password_hash):
        return None

    return agent
