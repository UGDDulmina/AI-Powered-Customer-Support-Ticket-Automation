from datetime import datetime
from enum import Enum

from app.services.agent_assignment_service import find_least_busy_agent

from pydantic import(
 BaseModel,
 ConfigDict,
 Field
)

class TicketPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class TicketStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"

class TicketBase(BaseModel):
    subject: str = Field(
        min_length=3,
        max_length=200
    )

    description: str = Field(
        min_length=10
    )

    priority: TicketPriority = Field(
        default= TicketPriority.MEDIUM
    )

    category: str | None = Field(
        max_length=50,
        default=None
    )

class TicketCreate(TicketBase):
    customer_id: int = Field(gt=0),
    priority: TicketPriority | None = None

    model_config=ConfigDict(
        extra="forbid"
    )

class TicketUpdate(TicketBase):
    status: TicketStatus 
    priority: TicketPriority

class TicketResponse(TicketBase):
    id: int
    customer_id: int 
    status: TicketStatus
    created_at: datetime
    assigned_agent_id: int | None

    model_config = ConfigDict(
        from_attributes=True
    )

class TicketStatusUpdate(BaseModel):
    status: TicketStatus 
    model_config = ConfigDict(
        extra="forbid"
    )

class TicketPriorityUpdate(BaseModel):
    priority: TicketPriority
    model_config = ConfigDict(
        extra="forbid"
    )

class TicketPaginatedResponse(BaseModel):
    item: list[TicketResponse]
    total: int
    page: int
    limit: int
    total_pages: int
    has_next: bool
    has_previous: bool

class TicketAssignRequest(BaseModel):
    agent_id: int = Field(
        gt=0
    )
    model_config = ConfigDict(
        extra="forbid"
    )

class TicketCategorizeRequest(BaseModel):
    subject: str = Field(
        min_length=1,
        max_length=225
    )
    description: str = Field(
        min_length=1
    )

class TicketCategorizeResponse(BaseModel):
    category: str

class TicketPriorityRequest(BaseModel):
    subject: str = Field(
        min_length=1,
        max_length=225
    )
    description: str = Field(
        min_length=1
    )

class TicketPriorityResponse(BaseModel):
    priority: TicketPriority
    matched_keywords: list[str]
    reason: str
    




