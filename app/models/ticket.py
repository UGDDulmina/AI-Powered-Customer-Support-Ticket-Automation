from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

from app.models.customer import Customer


class Ticket(Base):
    __tablename__ = "tickets"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    customer_id: Mapped[int] = mapped_column(
        ForeignKey("customers.id"),
        nullable=False,
        index=True
    )

    subject: Mapped[str] = mapped_column(
        String(200),
        nullable=False
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )

    status: Mapped[str] = mapped_column(
        String(30),
        default="open",
        nullable=False
    )

    priority: Mapped[str] = mapped_column(
        String(20),
        default="medium",
        nullable=False
    )

    category: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    customer: Mapped["Customer"] = relationship(
        back_populates="tickets"
    )

    messages: Mapped[list["TicketMessage"]] = relationship(
        back_populates="ticket"
    )