
from fastapi import APIRouter, Depends
from sqlalchemy import func, select

from app.db.dependencies import get_db
from app.models.ticket import Ticket
from app.schemas.stats import TicketStatusStatsResponse

from sqlalchemy.orm import Session

router = APIRouter(
    prefix="/stats",
    tags=["Statistics"]
)

@router.get(
    "/tickets/status",
    response_model=TicketStatusStatsResponse
)
def get_stats(
    database_session: Session = Depends(get_db)
):
    statement = (
        select(
           Ticket.status,
           func.count(Ticket.id)
        )
        .group_by(Ticket.status)
    )

    result = database_session.execute(statement).all()

    status_counts = {
        "open": 0,
        "in_progress": 0,
        "resolved": 0,
        "closed": 0
    }
    
    for status, count in result:
        status_counts[status] = count

    return status_counts

@router.get(
    "/tickets/priority",
    response_model=TicketStatusStatsResponse
)
def get_stats(
    database_session: Session = Depends(get_db)
):
    statement = (
        select(
           Ticket.priority,
           func.count(Ticket.id)
        )
        .group_by(Ticket.priority)
    )

    result = database_session.execute(statement).all()

    status_counts = {
        "low": 0,
        "medium": 0,
        "high": 0,
        "urgent": 0
    }
    
    for status, count in result:
        status_counts[status] = count

    return status_counts