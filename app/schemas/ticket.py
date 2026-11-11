from datetime import datetime
from enum import Enum

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
    customer_id: int = Field(gt=0)

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




