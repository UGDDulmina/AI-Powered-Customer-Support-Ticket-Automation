from sqlalchemy.exc import IntegrityError

from fastapi import (
    APIRouter,
    Path,
    status,
    Depends,
    HTTPException,
    Query
)
from sqlalchemy import select

from app.models.customer import Customer
from app.models.support_agent import SupportAgent
from app.models.ticket import Ticket

from sqlalchemy.orm import Session

from app.models.ticket_activity import TicketActivity
from app.schemas.ticket import (
    TicketAssignRequest,
    TicketResponse, 
    TicketCreate,
    TicketUpdate,
    TicketStatus,
    TicketStatusUpdate,
    TicketPriorityUpdate,
    TicketPriority,
    TicketPaginatedResponse
)
from app.db.dependencies import get_db 

from sqlalchemy import func, select

import math

from app.schemas.ticket_activity import TicketActivityAction

ALLOWED_STATUS = {
    TicketStatus.OPEN: {
        TicketStatus.IN_PROGRESS,
        TicketStatus.RESOLVED
    },
    TicketStatus.IN_PROGRESS: {
        TicketStatus.RESOLVED
    },
    TicketStatus.RESOLVED: {
        TicketStatus.CLOSED
    },
    TicketStatus.CLOSED: set()
}


router = APIRouter(
    prefix="/tickets",
    tags=["Tickets"]
)

@router.post(
    "",
    response_model= TicketResponse,
    status_code=status.HTTP_201_CREATED
)
def create_ticket(
    ticket_data: TicketCreate,
    database_session: Session = Depends(get_db)
):
    customer = database_session.get(
        Customer,
        ticket_data.customer_id
    )

    if customer is None:
        raise HTTPException(
           status_code=404,
           detail="Customer not found"
        )

    ticket = Ticket(
        customer_id = ticket_data.customer_id,
        description = ticket_data.description,
        priority = ticket_data.priority.value,
        category = ticket_data.category,
        status = TicketStatus.OPEN.value,
        subject = ticket_data.subject,
        customer = customer
    )

    database_session.add(ticket)

    try:
        database_session.flush()

        activity = TicketActivity(
            ticket_id=ticket.id,
            action = TicketActivityAction.CREATED.value,
            old_value = None,
            new_value = ticket.status,
            performed_by = "system"
        )

        database_session.add(activity)
        database_session.commit()
        database_session.refresh(ticket)

        database_session.refresh(ticket)
    except Exception:
        database_session.rollback()
        raise

    return ticket

@router.get(
        "/{ticket_id}",
        response_model=TicketResponse
)
def get_ticket(
    ticket_id: int = Path(gt=0),
    database_session: Session = Depends(get_db)
):
    ticket = database_session.get(Ticket, ticket_id)

    if ticket is None:
        raise HTTPException(
            status_code=404,
            detail="Ticket not found"
        )

    return ticket

 

@router.get(
    "",
    response_model=TicketPaginatedResponse
)
def get_tickets(
    assigned_agent_id: int | None = Query(
        default=None,
        ge=1
    ),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=10, ge=1, le=100),
    search: str | None = Query(
      default=None
    ),
    customer_id: int | None = Query(
        default=None,
        ge=1
    ),
    status: TicketStatus | None = Query(
        default=None
    ),
    priority: TicketPriority | None = Query(
        default=None
    ),
    database_session: Session = Depends(get_db)
):
    offset = (page - 1) * limit

    statement = select(Ticket)

    if search is not None:
        keyword = search.strip()

        if keyword:
          statement = statement.where(
             Ticket.subject.ilike(f"%{keyword}%")
          )

    if customer_id is not None:
        statement = statement.where(
            Ticket.customer_id == customer_id
        )
            
    if status is not None:
        statement = statement.where(
            Ticket.status == status.value
        )

    if priority is not None:
        statement = statement.where(
            Ticket.priority == priority.value
        )

    if assigned_agent_id is not None:
        statement = statement.where(
            Ticket.assigned_agent_id == assigned_agent_id
        )

    count_statement = select(func.count()).select_from(Ticket)

    total = database_session.scalar(count_statement)
    total_pages = math.ceil(total/limit)
    has_next = page < total_pages
    has_previous = page > 1

    statement = (
        statement
        .order_by(Ticket.id.desc())
        .offset(offset)
        .limit(limit)
    )

    tickets = database_session.scalars(statement).all()

    return {
        "items": tickets,
        "total": total,
        "page": page,
        "limit": limit,
        "total_pages": total_pages,
        "has_next": has_next,
        "has_previous":has_previous
    }

@router.put(
    "/{ticket_id}",
    response_model = TicketResponse
)
def update_ticket(
    ticket_id: int ,
    ticket_data: TicketUpdate,
    database_session: Session = Depends(get_db)
):
    ticket = database_session.get(Ticket, ticket_id)

    if ticket  is None :
        raise HTTPException(
            status_code=404,
            detail="Ticket not found"
        )
    update_ticket = ticket_data.model_dump(
        mode="json",
        exclude_unset=True
    )
    for field_name, value in update_ticket.items():
        setattr(ticket, field_name, value)

    try:
        database_session.commit()
        database_session.refresh(ticket)

    except IntegrityError:
        database_session.rollback()
        raise HTTPException(
            status_code=409,
            detail="Ticket update conflicts with database constraints"
        )

    return ticket 

@router.patch(
    "/{ticket_id}/status",
    response_model = TicketResponse
)
def status_update(
    status_data: TicketStatusUpdate,
    database_session: Session = Depends(get_db),
    ticket_id: int = Path(gt=0)
):
    ticket = database_session.get(Ticket, ticket_id)

    if ticket is None:
        raise HTTPException(
            status_code=404,
            detail="Ticket not found"
        )

    try:
       current_status = TicketStatus(ticket.status)

    except ValueError:
      
      raise HTTPException(
         status_code=409,
         detail="Current ticket status is invalid"
      )

    allowed = ALLOWED_STATUS.get(current_status, set())

    if status_data.status not in allowed:
     raise HTTPException(
        status_code=409,
        detail="Current ticket status is invalid"
     )

    old_status = ticket.status
    
    ticket.status = status_data.status.value

    activity = TicketActivity(
       ticket_id = ticket.id,
       action = TicketActivityAction.STATUS_CHANGED.value,
       old_value = old_status,
       new_value = status_data.status.value,
       performed_by = "system"
    )
    database_session.add(activity)

    try: 
        database_session.commit()
        database_session.refresh(ticket)
    except Exception:
        database_session.rollback()
        raise

    return ticket

@router.patch(
    "/{ticket_id}/priority",
    response_model=TicketResponse
)
def priority_update(
    priority_data: TicketPriorityUpdate,
    database_session: Session = Depends(get_db),
    ticket_id: int = Path(gt=0)
):
  ticket = database_session.get(Ticket, ticket_id)

  if ticket is None:
      raise HTTPException(
          status_code=404,
          detail="Ticket is not found"
      ) 

  old_priority = ticket.priority

  ticket.priority = priority_data.priority.value

  activity = TicketActivity(
      ticket_id = ticket.id,
      action = TicketActivityAction.PRIORITY_CHANGED.value,
      old_value= old_priority,
      new_value= priority_data.priority.value,
      performed_by = "system"
  )

  if old_priority == priority_data.priority.value:
      return ticket

  database_session.add(activity)
 
  try: 
        database_session.commit()
        database_session.refresh(ticket)
  except Exception:
        database_session.rollback()
        raise
  
  return ticket

@router.patch(
    "/{ticket_id}/assign",
    response_model=TicketResponse
)
def assign_agent(
    ticket_id: int,
    assignment_data: TicketAssignRequest, 
    database_session: Session = Depends(get_db)
):
    ticket = database_session.get(Ticket,ticket_id)

    if ticket is None:
        raise HTTPException(
            status_code=404,
            detail="Not found"
        )

    agent = database_session.get(SupportAgent, 
                    assignment_data.agent_id)

    if agent is None:
        raise HTTPException(
            status_code=404,
            detail="Not found"
        )
    if not agent.is_active:
        raise HTTPException(
            status_code=409,
            detail="Not found"
        )
    ticket.assigned_agent = agent
    ticket.assigned_agent_id = agent.id

    old_agent_id = ticket.assigned_agent_id
    new_agent_id = agent.id

    if old_agent_id == new_agent_id:
        return ticket
    if old_agent_id is None:
        action = TicketActivityAction.ASSIGNED.value
    else:
        if old_agent_id != new_agent_id:
            ticket.assigned_agent_id = new_agent_id

    activity = TicketActivity(
          ticket_id = ticket.id,
          action = action,
          old_value= old_agent_id,
          new_value= new_agent_id,
          performed_by = "system"
      )

    database_session.commit()
    database_session.refresh(ticket)

    return ticket


    
    