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
    TicketStatus
)
from app.db.dependencies import get_db 

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
    database_session: Session = Depends(get_db)
):
    offset = (page - 1) * limit

    statement = select(Ticket)

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
    