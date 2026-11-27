from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class AIAutomationJobResponse(BaseModel):
    id: int
    ticket_id:int
    status:str
    attempt_count: int
    error_message:str | None
    crated_at: datetime = Field(validation_alias="created_at")
    started_at: datetime | None
    completed_at: datetime | None
    

    model_config = ConfigDict(
        from_attributes=True
    )
