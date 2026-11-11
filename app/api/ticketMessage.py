from fastapi import (
    APIRouter,
    Path,
    status,
    Depends,
    HTTPException,
    Query
)

from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.ticket import Ticket
from app.models.ticket_message import TicketMessage

from app.db.dependencies import get_db

from app.schemas.ticket_message import(
    TicketMessageResponse,
    TicketMessageCreate,
    MessageSenderType,
    Order
)


router = APIRouter(
    prefix="/tickets",
    tags=["TicketMessage"]

)

@router.post(
    "/{ticket_id}/messages",
    response_model=TicketMessageResponse,
    status_code=status.HTTP_201_CREATED
)
def create_message(
    message_data:TicketMessageCreate,
    ticket_id: int = Path(gt=0),
    database_session: Session = Depends(get_db)
):
    ticket = database_session.get(
        Ticket,
        ticket_id
    )

    if ticket is None:
        raise HTTPException(
            status_code=404,
            detail="Ticket not found"
        )

    message = TicketMessage(
        ticket_id=ticket_id,
        sender_type=message_data.sender_type.value,
        content=message_data.content
    )

    database_session.add(message)

    try:
        database_session.commit()
        database_session.refresh(message)
    except Exception:
        database_session.rollback()
        raise

    return message



@router.get(
    "/{ticket_id}/messages",
    response_model=list[TicketMessageResponse]
)
def get_messages(
    ticket_id: int,
    order: Order = Query(
        default=Order.ASC
    ),
    sender_type: MessageSenderType | None = Query(
        default=None
    ),
    database_session: Session = Depends(get_db)
):
    ticket = database_session.get(Ticket, ticket_id)

    if ticket is None:
        raise HTTPException(
            status_code=404,
            detail="Ticket Not Found"
        )
    
    statement = select(TicketMessage).where(
        TicketMessage.ticket_id == ticket_id
    )

    if sender_type is not None:
        statement = statement.where(
            TicketMessage.sender_type == sender_type.value
        )

    if order is Order.DESC:
        statement = statement.order_by(
           TicketMessage.created_at.desc(),
           TicketMessage.id.desc()
        )
    else:
        statement = statement.order_by(
            TicketMessage.created_at.asc(),
            TicketMessage.id.asc()
        )


    messages = database_session.scalars(statement).all()

    return messages