from typing import Literal
from pydantic import BaseModel, EmailStr, Field, ConfigDict


class AgentRegistrationRequest(BaseModel):
    name: str = Field(min_length=2, max_length=150)
    email: EmailStr
    password: str = Field(min_length=12, max_length=128)
    role: Literal["admin", "agent"] = "agent"


class AgentRegistrationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: EmailStr
    role: str
    is_active: bool