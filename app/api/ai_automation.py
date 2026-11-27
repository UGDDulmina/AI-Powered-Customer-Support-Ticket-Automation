from app.core.auth_dependencies import get_current_agent, require_admin
from app.core.ticket_permissions import ensure_ticket_access
from app.models.ticket import Ticket
from app.models.support_agent import SupportAgent
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from app.db.dependencies import get_db
from app.models.ai_automation_job import AIAutomationJob
from app.schemas.ai_automation_job import AIAutomationJobResponse

from sqlalchemy import update

from app.services.ticket_automation_service import (
    process_ai_automation_job
)

router = APIRouter(
    prefix="/ai-automation",
    tags=["AI Automation"]
)


@router.get(
    "/jobs/{job_id}",
    response_model=AIAutomationJobResponse
)
def get_automation_job(
    job_id: int,
    database_session: Session = Depends(get_db),
    current_agent: SupportAgent = Depends(get_current_agent)
):

    job = database_session.get(
        AIAutomationJob,
        job_id
    )

    if job is None:
        raise HTTPException(
            status_code=404,
            detail="Automation job not found"
        )

    ticket = database_session.get(Ticket, job.ticket_id)
    if ticket is None:
        raise HTTPException(status_code=404, detail="Ticket not found")
    ensure_ticket_access(ticket, current_agent)
    return job

MAX_ATTEMPTS = 3

@router.post(
    "/jobs/{job_id}/retry",
    response_model=AIAutomationJobResponse
)
def retry_automation_job(
    job_id: int,
    background_tasks: BackgroundTasks,
    database_session: Session = Depends(get_db),
    current_agent: SupportAgent = Depends(require_admin)
):
    job = database_session.get(AIAutomationJob, job_id)

    if job is None:
        raise HTTPException(
            status_code=404,
            detail="Automation job not found"
        )

    if job.status != "failed":
        raise HTTPException(
            status_code=409,
            detail="Only failed jobs can be retried"
        )
 
    if job.attempt_count >= MAX_ATTEMPTS:
        raise HTTPException(
            status_code=409,
            detail="Maximum retry attempts reached"
        )

    statement = (
        update(AIAutomationJob)
        .where(
            AIAutomationJob.id == job_id,
            AIAutomationJob.status == "failed",
            AIAutomationJob.attempt_count < MAX_ATTEMPTS
        )
        .values(
            status="pending",
            error_message=None,
            started_at=None,
            completed_at=None
        )
        .execution_options(synchronize_session="fetch")
    )

    result = database_session.execute(statement)

    if result.rowcount != 1:
        database_session.rollback()

        raise HTTPException(
            status_code=409,
            detail="Job is no longer eligible for retry"
        )

    database_session.commit()

    database_session.refresh(job)


    background_tasks.add_task(
        process_ai_automation_job,
        job_id
    )

    return job
