from pydantic import(
    BaseModel,
    Field,
    ConfigDict
)

from enum import Enum

from datetime import datetime

class MessageSenderType(str , Enum):
    CUSTOMER = "customer"
    AGENT ="agent"
    AI = "ai"

class Order(str, Enum):
    ASC = "asc",
    DSC = "dsc"

class TicketMessageBase(BaseModel):
    sender_type: MessageSenderType
    content: str = Field(
        min_length=1,
        max_length=5000
    )

class TicketMessageCreate(TicketMessageBase):
    model_config = ConfigDict(extra="forbid")

class TicketMessageResponse(TicketMessageBase):
    id: int
    ticket_id: int
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )
