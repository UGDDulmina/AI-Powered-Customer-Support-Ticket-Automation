from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    ForeignKey
)

from app.db.base import Base  # Adjust to your existing Base import


class AIReplySuggestion(Base):
    __tablename__ = "ai_reply_suggestions"

    id = Column(
        Integer,
        primary_key=True,
    )

    ticket_id = Column(
        Integer,
        ForeignKey("tickets.id"),
        nullable=False,
        index=True
    )

    suggested_reply = Column(
        Text
    )

    edited_reply = Column(
        Text,
        nullable=True
    )

    status = Column(
        String(20),
        default="pending",
        nullable=False,
        index=True
    )

    reviewed_by_agent_id = Column(
        Integer,
        ForeignKey("support_agents.id"),
        nullable=True
    )

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    
    reviewed_at = Column(
        DateTime(timezone=True),
        nullable=True
    )