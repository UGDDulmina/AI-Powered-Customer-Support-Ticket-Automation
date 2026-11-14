from sqlalchemy import and_, select, func
from sqlalchemy.orm import Session

from app.models.support_agent import SupportAgent
from app.models.ticket import Ticket

# def count_tickets_for_agent(agent:SupportAgent , database_session: Session):

#     statement = (
#         select(func.count(Ticket.id))
#         .where(
#             Ticket.assigned_agent_id == agent.id,
#             Ticket.status.in_(["open","in_progress"])
#         )
#     )

#     ticket_count = database_session.scalar(statement)

#     return ticket_count

def find_least_busy_agent(
        database_session: Session
) -> SupportAgent | None:

            statement = (
                        select(SupportAgent)
                        .outerjoin(
                            Ticket,
                            and_(
                                Ticket.assigned_agent_id == SupportAgent.id,
                                Ticket.status.in_(["open", "in_progress"])
                            )
                        )
                        .where(SupportAgent.is_active.is_(True))
                        .group_by(SupportAgent.id)
                        .order_by(
                            func.count(Ticket.id).asc(),
                            SupportAgent.id.asc()
                        )
                        .limit(1)
                    )

            selected_agent = database_session.scalars(statement).first()

            return selected_agent