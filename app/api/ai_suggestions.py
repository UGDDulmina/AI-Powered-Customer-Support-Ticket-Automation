from app.core.auth_dependencies import get_current_agent
from app.core.ticket_permissions import ensure_ticket_access
from app.models.ticket import Ticket
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.dependencies import get_db

from app.models.ai_reply_suggestion import AIReplySuggestion
from app.models.support_agent import SupportAgent
from app.models.ticket_message import TicketMessage

from app.schemas.ai_suggetion import (
    AIReplySendRequest,
    AIReplySendResponse
)

router = APIRouter(
    prefix="/ai-suggestions",
    tags=["AI Suggestions"]
)


@router.post(
    "/{suggestion_id}/send",
    response_model=AIReplySendResponse
)
def send_approved_ai_reply(
    suggestion_id: int,
    payload: AIReplySendRequest,
    database_session: Session = Depends(get_db),
    current_agent: SupportAgent = Depends(get_current_agent)
):
    try:
        
        statement = (
            select(AIReplySuggestion)
            .where(AIReplySuggestion.id == suggestion_id)
            .with_for_update()
        )

        suggestion = database_session.scalar(statement)

        if suggestion is None:
            raise HTTPException(
                status_code=404,
                detail="AI suggestion not found"
            )

        ticket = database_session.get(Ticket, suggestion.ticket_id)
        if ticket is None:
            raise HTTPException(status_code=404, detail="Ticket not found")
        ensure_ticket_access(ticket, current_agent)
        if payload.agent_id != current_agent.id:
            raise HTTPException(status_code=403, detail="Agent identity mismatch")
        if suggestion.status != "approved":
            raise HTTPException(status_code=409, detail="Only approved suggestions can be sent")
        agent = current_agent

        if suggestion.reviewed_by_agent_id != agent.id:
            raise HTTPException(
                status_code=403,
                detail="Only the reviewing agent can send this suggestion"
            )

         
        message_content = (
            suggestion.edited_reply
            if suggestion.edited_reply is not None
            else suggestion.suggested_reply
        )

        if not message_content or not message_content.strip():
            raise HTTPException(
                status_code=422,
                detail="Message content cannot be empty"
            )

       
        message = TicketMessage(
            ticket_id=suggestion.ticket_id,
            sender_type="agent",
            content=message_content.strip()
        )

        database_session.add(message)
        database_session.flush()

        
        suggestion.status = "sent"

         
        database_session.commit()

        return AIReplySendResponse(
            suggestion_id=suggestion.id,
            ticket_id=suggestion.ticket_id,
            message_id=message.id,
            status=suggestion.status,
            sender_type=message.sender_type
        )

    except HTTPException:
        database_session.rollback()
        raise

    except SQLAlchemyError:
        database_session.rollback()
        raise HTTPException(
            status_code=500,
            detail="Failed to send approved AI reply"
        )
