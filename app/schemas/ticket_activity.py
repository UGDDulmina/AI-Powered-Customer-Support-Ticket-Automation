from datetime import datetime

from pydantic import (
    BaseModel,
    Field,
    ConfigDict
)

from enum import Enum

class TicketActivityAction(str , Enum):
    CREATED = "created",
    ASSIGNED = "assigned",
    REASSIGNED = "reassigned",
    STATUS_CHANGED = "status_changed",
    PRIORITY_CHANGED = "priority_changed"
    
class TicketActivityCreate(BaseModel):

    ticket_id: int = Field(
        gt=0
    )
    action: TicketActivityAction
    old_value: str | None = Field(
        default=None,
        max_length=225
    )
    new_value: str | None = Field(
        default=None,
        max_length=225
    ) 
    performed_by: str = Field(
        max_length=50
    )

class TicketActivityResponse(BaseModel):   
    id: int
    ticket_id: int
    action: TicketActivityAction
    old_value: str | None
    new_value: str | None
    performed_by: str
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )