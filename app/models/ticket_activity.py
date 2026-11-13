
from sqlalchemy import (
    ForeignKey, 
    String,
    DateTime,
    func
    )

from app.db.base import Base

from sqlalchemy.orm import (
    Mapped, 
    mapped_column,
    relationship
)

from datetime import datetime

from app.models.ticket import Ticket


class TicketActivity(Base):

    __tablename__ = "ticket_activities"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )
    ticket_id: Mapped[int] = mapped_column(
        ForeignKey("tickets.id"),
        nullable=False,
        index=True
    )
    action: Mapped[str] = mapped_column(
        String[50],
        nullable=False
    )
    old_value: Mapped[str | None] = mapped_column(
        String[225],
        nullable=True
    )
    new_value: Mapped[str | None] = mapped_column(
        String[225],
        nullable=True
    )
    performed_by: Mapped[str] = mapped_column(
        String[50],
        nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    ticket: Mapped[Ticket] = relationship(
        back_populates = "ticket_activites"
    )
