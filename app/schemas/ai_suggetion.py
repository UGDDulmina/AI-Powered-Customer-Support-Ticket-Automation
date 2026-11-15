from pydantic import BaseModel, Field


class AIReplySendRequest(BaseModel):
    agent_id: int = Field(gt=0)


class AIReplySendResponse(BaseModel):
    suggestion_id: int
    ticket_id: int
    message_id: int
    status: str
    sender_type: str