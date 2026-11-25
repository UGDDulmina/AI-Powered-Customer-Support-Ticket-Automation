from datetime import datetime
from enum import Enum
from typing import Literal

from app.models.ai_reply_suggestion import AIReplySuggestion

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
    items: list[TicketResponse]
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

class TicketReplySuggestionResponse(BaseModel):
    id:int
    status: str
    ticket_id: int
    subject: str
    suggested_reply: str

class AIReplySuggestionListResponse(BaseModel):
    id:int
    ticket_id:int
    suggested_reply: str
    edited_reply: str | None
    status:str
    created_at:datetime

class AIReplyReviewRequest(BaseModel):
    agent_id:int = Field(gt=0)
    action: Literal["approve","reject"]
    edited_reply: str | None = None

class AIReplyReviewResponse(BaseModel):
    id: int
    ticket_id: int
    status: str
    suggested_reply: str
    edited_reply: str | None = None
    reviewed_by_agent_id: int
    reviewed_at: datetime
    




