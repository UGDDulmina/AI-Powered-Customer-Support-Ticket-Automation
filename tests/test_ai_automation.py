
from unittest.mock import patch
from sqlalchemy import select
from sqlalchemy.orm import Session
 
from app.models.ai_automation_job import AIAutomationJob
from app.models.ai_reply_suggestion import AIReplySuggestion
from app.db.session import SessionLocal

from unittest.mock import patch
from sqlalchemy import select, func

from app.services.ticket_automation_service import (
    process_ai_automation_job
)
from app.models.ai_reply_suggestion import AIReplySuggestion

from app.services.ticket_automation_service import process_ai_automation_job

from app.models.ai_automation_job import AIAutomationJob
from unittest.mock import patch


 

def test_ai_automation_job_created(
    client,
    created_customer,
    db_session
):
    customer_id = created_customer["id"]

    
    with patch(
        "fastapi.background.BackgroundTasks.add_task"
    ) as mock_add_task:

        response = client.post(
            "/api/v1/tickets",
            json={
                "customer_id": customer_id,
                "subject": "Unable to log in",
                "description": "I cannot access my account."
            }
        )

    assert response.status_code in (200, 201), response.text

    ticket_id = response.json()["id"]

    
    job = db_session.scalar(
        select(AIAutomationJob)
        .where(AIAutomationJob.ticket_id == ticket_id)
    )

    assert job is not None
    assert job.ticket_id == ticket_id
    assert job.status == "pending"
    assert job.attempt_count == 0


    mock_add_task.assert_called_once()


def test_ai_automation_job_processes_successfully(
    created_ticket,
    db_session
):
    ticket_id = created_ticket["id"]

    job = AIAutomationJob(
        ticket_id=ticket_id,
        status="pending",
        attempt_count=0
    )

    db_session.add(job)
    db_session.flush()

    job_id = job.id

    fake_reply = (
        "Thank you for contacting support. "
        "We will help you resolve this issue."
    )

    with patch(
        "app.services.ticket_automation_service.SessionLocal"
    ) as mock_session_factory, patch(
        "app.services.ticket_automation_service.generate_ticket_reply",
        return_value=fake_reply
    ) as mock_generate:

        mock_session_factory.return_value = db_session

        process_ai_automation_job(job_id)

    db_session.expire_all()

    updated_job = db_session.get(AIAutomationJob, job_id)

    suggestion = db_session.scalar(
        select(AIReplySuggestion)
        .where(AIReplySuggestion.ticket_id == ticket_id)
    )

    assert updated_job.status == "completed"
    assert updated_job.error_message is None

    assert suggestion is not None
    assert suggestion.status == "pending"
    assert suggestion.suggested_reply == fake_reply

    mock_generate.assert_called_once()


def test_ai_automation_handles_ai_failure(
    created_ticket,
    db_session
):
    ticket_id = created_ticket["id"]

    job = AIAutomationJob(
        ticket_id=ticket_id,
        status="pending",
        attempt_count=0
    )

    db_session.add(job)
    db_session.flush()

    job_id = job.id

    with patch(
        "app.services.ticket_automation_service.SessionLocal",
        return_value=db_session
    ), patch(
        "app.services.ticket_automation_service.generate_ticket_reply",
        side_effect=RuntimeError("Simulated AI service failure")
    ) as mock_generate:

        process_ai_automation_job(job_id)

        mock_generate.assert_called_once()

    db_session.expire_all()

    updated_job = db_session.get(AIAutomationJob, job_id)

    assert updated_job is not None
    assert updated_job.attempt_count >= 1
    assert updated_job.status in ("pending", "failed")

def test_ai_automation_increments_attempt_count(
    created_ticket,
    db_session
):
    ticket_id = created_ticket["id"]

    job = AIAutomationJob(
        ticket_id=ticket_id,
        status="pending",
        attempt_count=0
    )

    db_session.add(job)
    db_session.flush()

    job_id = job.id

    with patch(
        "app.services.ticket_automation_service.SessionLocal",
        return_value=db_session
    ):
 
        with patch(
            "app.services.ticket_automation_service.generate_ticket_reply",
            side_effect=RuntimeError("Simulated AI failure")
        ) as mock_generate:

            process_ai_automation_job(job_id)

            mock_generate.assert_called_once()

    db_session.expire_all()

    updated_job = db_session.get(AIAutomationJob, job_id)

    assert updated_job is not None
    assert updated_job.attempt_count == 1

def test_ai_automation_invalid_job_id(db_session):

    invalid_job_id = -1

    suggestions_before = db_session.scalar(
        select(func.count(AIReplySuggestion.id))
    )

    with patch(
        "app.services.ticket_automation_service.SessionLocal",
        return_value=db_session
    ):

        process_ai_automation_job(invalid_job_id)

    db_session.expire_all()


    suggestions_after = db_session.scalar(
        select(func.count(AIReplySuggestion.id))
    )

    assert suggestions_after == suggestions_before


def test_completed_ai_automation_job_cannot_process_again(
    created_ticket,
    db_session
):
    ticket_id = created_ticket["id"]

    job = AIAutomationJob(
        ticket_id=ticket_id,
        status="completed",
        attempt_count=1
    )

    db_session.add(job)
    db_session.flush()

    job_id = job.id

    suggestions_before = db_session.scalar(
        select(func.count(AIReplySuggestion.id))
        .where(AIReplySuggestion.ticket_id == ticket_id)
    )

    fake_reply = (
        "Thank you for contacting support. "
        "We will help you resolve this issue."
    )

  
    with patch(
        "app.services.ticket_automation_service.SessionLocal",
        side_effect=lambda: Session(
            bind=db_session.connection(),
            join_transaction_mode="create_savepoint"
        )
    ), patch(
        "app.services.ticket_automation_service.generate_ticket_reply",
        return_value = fake_reply
    ) as mock_generate:

        process_ai_automation_job(job_id)

      
        mock_generate.assert_not_called()


    db_session.expire_all()

    updated_job = db_session.get(AIAutomationJob, job_id)

    suggestions_after = db_session.scalar(
        select(func.count(AIReplySuggestion.id))
        .where(AIReplySuggestion.ticket_id == ticket_id)
    )

  
    assert updated_job.status == "completed"
    assert updated_job.attempt_count == 1

  
    assert suggestions_after == suggestions_before


