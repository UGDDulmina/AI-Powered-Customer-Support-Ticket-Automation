from pydantic import (
    BaseModel,
    EmailStr,
    Field,
    ConfigDict,
    field_validator
)


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

    model_config = ConfigDict(
        from_attributes=True
    )


class AgentProfileUpdateRequest(BaseModel):
    name: str = Field(
        min_length=2,
        max_length=100
    )

    email: EmailStr

    current_password: str | None = Field(
        default=None,
        min_length=1
    )

    model_config = ConfigDict(
        extra="forbid"
    )

    @field_validator("name", mode="before")
    @classmethod
    def normalize_name(cls, value):
        if isinstance(value, str):
            return value.strip()

        return value

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value):
        normalized = value.strip().lower()

        if len(normalized) > 255:
            raise ValueError(
                "Email cannot exceed 255 characters"
            )

        return normalized


class AgentChangePasswordRequest(BaseModel):
    current_password: str = Field(
        min_length=1
    )

    new_password: str = Field(
        min_length=12,
        max_length=128
    )

    model_config = ConfigDict(
        extra="forbid"
    )

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, value):
        if not value.strip():
            raise ValueError(
                "Password cannot contain only spaces"
            )

        return value


class PasswordChangeResponse(BaseModel):
    message: str