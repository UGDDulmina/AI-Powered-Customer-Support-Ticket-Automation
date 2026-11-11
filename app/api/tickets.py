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
from app.models.ticket import Ticket

from sqlalchemy.orm import Session

from app.schemas.ticket import (
    TicketResponse, 
    TicketCreate,
    TicketUpdate,
    TicketStatus,
    TicketStatusUpdate,
    TicketPriorityUpdate,
    TicketPriority
)
from app.db.dependencies import get_db 

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
        database_session.commit()
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
    response_model=list[TicketResponse]
)
def get_tickets(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=10, ge=1, le=100),
    search: str | None = Query(
      default=None
    ),
    customer_id: int | None = Query(
        default=None,
        min_length=1
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

    

    statement = (
        statement
        .order_by(Ticket.id.desc())
        .offset(offset)
        .limit(limit)
    )

    tickets = database_session.scalars(statement).all()

    return tickets

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

    allowed = ALLOWED_STATUS.get(ticket.status)

    if status_data.status not in allowed:
     raise HTTPException(
        status_code=409,
        detail="Current ticket status is invalid"
     )
    ticket.status = status_data.status.value

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

  ticket.priority = priority_data.priority.value

  try: 
        database_session.commit()
        database_session.refresh(ticket)
  except Exception:
        database_session.rollback()
        raise
  
  return ticket



    
    