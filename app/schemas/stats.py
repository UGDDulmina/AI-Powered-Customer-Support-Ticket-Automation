
from pydantic import BaseModel, Field


class TicketStatusStatsResponse(BaseModel):
    open: int = Field(
        default=0
    )
    in_progress: int = Field(
        default=0
    )
    resolved: int = Field(
        default=0
    )
    closed: int = Field(
        default=0
    )

class TicketPriorityStatsResponse(BaseModel):
    low: int = Field(
        default=0
    )
    medium: int = Field(
        default=0
    )
    high: int = Field(
        default=0
    )
    urgent: int = Field(
        default=0
    )

class TicketOverviewStatsResponse(BaseModel):
    total_tickets: int = Field(
        default=0
    )
    active_tickets: int = Field(
        default=0
    )
    completed_tickets: int = Field(
        default=0
    )
    resolution_rate: float = Field(
        default=0
    )

class DashboardStatsResponse(BaseModel):

    overview: TicketOverviewStatsResponse
    by_status: TicketStatusStatsResponse
    by_priority: TicketPriorityStatsResponse 

