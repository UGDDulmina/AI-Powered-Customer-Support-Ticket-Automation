from fastapi import HTTPException, status

from app.models.ticket import Ticket
from app.models.support_agent import SupportAgent


def ensure_ticket_access(
    ticket: Ticket,
    current_agent: SupportAgent
) -> None:

    if not current_agent.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive account"
        )

    if current_agent.role == "admin":
        return

    if (
        current_agent.role == "agent"
        and ticket.assigned_agent_id == current_agent.id
    ):
        return

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You do not have permission to access this ticket"
    )


def resolve_agent_scope(
    current_agent: SupportAgent,
    assigned_agent_id: int | None = None
) -> int | None:

    if not current_agent.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive account"
        )

    if current_agent.role == "admin":
        return assigned_agent_id

    if current_agent.role != "agent":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    if (
        assigned_agent_id is not None
        and assigned_agent_id != current_agent.id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot access another agent's tickets"
        )

    return current_agent.id