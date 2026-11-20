
from pydantic import BaseModel, EmailStr, Field


class AgentLoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class AuthenticatedAgentResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    role: str
    is_active: bool
