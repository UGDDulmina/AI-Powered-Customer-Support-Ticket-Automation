
from datetime import datetime, timezone

from fastapi import HTTPException, logger
from sqlalchemy import select
import logging

from app.db.session import SessionLocal
from app.models.ai_automation_job import AIAutomationJob
from app.models.ai_reply_suggestion import AIReplySuggestion
from app.models.ticket import Ticket
from app.models.ticket_message import TicketMessage
from app.services.ai_response_service import format_conversation_history, generate_ticket_reply
from app.services.ai_response_validator import validate_ai_reply


logger = logging.getLogger(__name__)


def generate_ai_suggestion_for_ticket(ticket_id: int)-> None:
    database_session = SessionLocal()

    try:
        ticket = database_session.get(Ticket, ticket_id)

        if ticket is None:
            logger.warning("Ticket %s not found", ticket_id)
            return

        statement = (
            select(TicketMessage)
            .where(TicketMessage.ticket_id == ticket_id)
            .order_by(
                TicketMessage.created_at.asc(),
                TicketMessage.id.asc()
            )
        )

        messages = database_session.scalars(statement).all()

        conversation_history = format_conversation_history(messages)

        ticket_reply = generate_ticket_reply(
            ticket.subject,
            ticket.description,
            conversation_history
        )

        validate = validate_ai_reply(ticket_reply)

        if not validate["is_valid"]:
            logger.warning(
                "AI reply validation failed for ticket %s: %s",
                ticket_id,
                validate["reason"]
            )
            return
        reply_suggestion = AIReplySuggestion(
            ticket_id=ticket.id,
            suggested_reply=ticket_reply,
            status="pending"
        )

        database_session.add(reply_suggestion)
        database_session.commit()

    except Exception:

        database_session.rollback()
        logger.exception(
            "Failed to generate AI suggestion for ticket %s",
            ticket_id
           )
    finally: 
        database_session.close()

def process_ai_automation_job(job_id: int) -> None:
    
    database_session = SessionLocal()

    try: 
        job = database_session.get(AIAutomationJob , job_id)

        if job is None:
           logger.warning("AI automation job %s not found", job_id)
           return

        if job.status != "pending":
           logger.warning(
                "Job %s cannot be processed. Current status: %s",
                job_id,
                job.status
            )
           return
        
        job.status = "processing"

        job.attempt_count += 1

        job.started_at = datetime.now(timezone.utc)

        job.error_message = None

        database_session.commit()

        ticket = database_session.get(
            Ticket,
            job.ticket_id
        )

        if ticket is None:
            raise ValueError("Associated ticket not found")

        statement = (
                    select(TicketMessage)
                    .where(TicketMessage.ticket_id == job.ticket_id)
                    .order_by(
                        TicketMessage.created_at.asc(),
                        TicketMessage.id.asc()
                    )
                )
        
        messages = database_session.scalars(statement).all()
        
        conversation_history = format_conversation_history(messages)

        ticket_reply = generate_ticket_reply(
                ticket.subject,
                ticket.description,
                conversation_history=conversation_history
        )

        validation_result = validate_ai_reply(ticket_reply)

        if not validation_result["is_valid"]:
            raise ValueError("AI reply failed validation")

        reply_suggestion = AIReplySuggestion(
            ticket_id=ticket.id,
            suggested_reply=ticket_reply,
            status="pending"
        )
        
        database_session.add(reply_suggestion)
        
        job.status = "completed"

        job.completed_at = datetime.now(timezone.utc)

        job.error_message = None

        

        database_session.commit()
        database_session.refresh(reply_suggestion)

    except Exception:
    
            database_session.rollback()

            logger.exception(
            "AI automation job %s failed",
            job_id
        )

            try:
                job = database_session.get(AIAutomationJob, job_id)

                if job is not None and job.status == "processing":
                    job.status = "failed"
                    job.error_message = "AI suggestion generation failed"
                    job.completed_at = datetime.now(timezone.utc)

                    database_session.commit()

            except Exception:
                database_session.rollback()

                logger.exception(
                    "Could not save failure status for job %s",
                    job_id
                )

    finally:
            database_session.close()

 


