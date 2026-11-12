
from datetime import datetime

from app.db.base import Base

from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Boolean, String, DateTime


class SupportAgent(Base):
    __tablename__ = "support_agents"

    id: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False
    )

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True
    ),
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
    ),
    created_at: Mapped[DateTime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )