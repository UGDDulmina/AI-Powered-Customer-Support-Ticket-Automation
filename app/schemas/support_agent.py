from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict, EmailStr

class SupportAgentBase(BaseModel):
    name: str = Field(
        min_length=2,
        max_length=100
    )

    email: EmailStr

class SupportAgentCreate(SupportAgentBase):
    model_config = ConfigDict(
        extra="forbid"
    )

class SupportAgentUpdate(BaseModel):
    name: str | None = Field(
        default=None,
        min_length=2,
        max_length=100
    )
    email: EmailStr | None = Field(
        default=None
    )
    is_active: bool | None = Field(
        default=None
    )
    model_config = ConfigDict(
        extra="forbid"
    )

class SupportAgentResponse(SupportAgentBase):
    id: int
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )
