
from fastapi import APIRouter, Depends
from sqlalchemy import func, select

from app.db.dependencies import get_db
from app.models.ticket import Ticket
from app.schemas.stats import (
    TicketOverviewStatsResponse,
    TicketStatusStatsResponse,
    TicketPriorityStatsResponse,
    DashboardStatsResponse
    )

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
    response_model=TicketPriorityStatsResponse
)
def get_stats_priority(
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

    priority_counts = {
        "low": 0,
        "medium": 0,
        "high": 0,
        "urgent": 0
    }
    
    for priority, count in result:
        priority_counts[priority] = count

    return priority_counts

@router.get(
    "/tickets/overview",
    response_model=TicketOverviewStatsResponse
)
def get_stats_overview(
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

    total = sum(status_counts.values())
    total_act = (status_counts["open"] + status_counts["in_progress"])
    total_com = (status_counts["resolved"] + status_counts["closed"])
    reso_rate = (round((total_com / total) * 100)if total>0 else 0.0)


    return {
        "total_tickets":total,
        "active_tickets":total_act,
        "completed_tickets":total_com,
        "resolution_rate":reso_rate
    }

@router.get(
    "/dashboard",
    response_model= DashboardStatsResponse
)
def get_final_stat(
    database_session: Session = Depends(get_db)
):
    status_statement = (
        select(
            Ticket.status,
            func.count(Ticket.id)
        )
        .group_by(Ticket.status)
    )

    priority_statement = (
        select(
            Ticket.priority,
            func.count(Ticket.id)
        )
        .group_by(Ticket.priority)
    )

    count_by_status = database_session.execute(status_statement).all()
    count_by_priority = database_session.execute(priority_statement).all()

    status_count = {
        "open": 0,
        "in_progress": 0,
        "resolved": 0,
        "closed": 0
    }

    priority_counts = {
        "low": 0,
        "medium": 0,
        "high": 0,
        "urgent": 0
    }

    for status,count in count_by_status:
        status_count[status] = count

    for priority,count in count_by_priority:
        priority_counts[priority] = count

    total = sum(status_count.values())
    active = (status_count['open'] + status_count["in_progress"])
    completed = (status_count["resolved"] + status_count["closed"])
    reso_rate = (
        round((completed/total)*100,2) 
        if total>0 
        else 0.0
        )

    return{
        "overview": {
             "total_tickets":total,
             "active_tickets":active,
             "completed_tickets":completed,
             "resolution_rate":reso_rate
        },
        "by_status": status_count,
        "by_priority": priority_counts
    }
