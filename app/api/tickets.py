from datetime import datetime, timezone

from fastapi import BackgroundTasks
from app.schemas.ai_automation_job import AIAutomationJobResponse
from app.services.ticket_automation_service import (
    generate_ai_suggestion_for_ticket
)

from app.models.ai_automation_job import AIAutomationJob

from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from app.models.ai_reply_suggestion import AIReplySuggestion
from app.models.ticket_message import TicketMessage
from app.services.agent_assignment_service import find_least_busy_agent
from app.services.ai_response_validator import validate_ai_reply

from fastapi import (
    APIRouter,
    Path,
    status,
    Depends,
    HTTPException,
    Query
)
from sqlalchemy import select

from app.services.ai_response_service import format_conversation_history, generate_ticket_reply
from app.services.ticket_priprity_predictor import (
    predict_ticket_priority,
    explain_ticket_priority
)

from app.models.customer import Customer
from app.models.support_agent import SupportAgent
from app.models.ticket import Ticket

from sqlalchemy.orm import Session
from app.services.ticket_categorizer import categorize_ticket

from app.models.ticket_activity import TicketActivity
from app.schemas.ticket import (
    AIReplyReviewRequest,
    AIReplySuggestionListResponse,
    AIReplyReviewRequest,
    TicketAssignRequest,
    TicketPriorityRequest,
    TicketPriorityResponse,
    TicketReplySuggestionResponse,
    TicketResponse, 
    TicketCreate,
    TicketUpdate,
    TicketStatus,
    TicketStatusUpdate,
    TicketPriorityUpdate,
    TicketPriority,
    TicketPaginatedResponse,
    TicketCategorizeResponse,
    TicketCategorizeRequest,
    AIReplyReviewResponse
)
from app.db.dependencies import get_db 

from sqlalchemy import func, select

import math

from app.schemas.ticket_activity import (
    TicketActivityAction, 
    TicketActivityResponse
)

from app.services.ticket_categorizer import categorize_ticket
from app.core.auth_dependencies import get_current_agent

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
    tags=["Tickets"],
    dependencies=[Depends(get_current_agent)],
)

@router.post(
    "",
    response_model= TicketResponse,
    status_code=status.HTTP_201_CREATED
)
def create_ticket(
    ticket_data: TicketCreate,
    background_tasks: BackgroundTasks,
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

    predicted_category = categorize_ticket(
        subject= ticket_data.subject,
        description=ticket_data.description
    )

    if ticket_data.priority is not None:
        final_priority = ticket_data.priority.value
    else:
        final_priority = predict_ticket_priority(
            subject=ticket_data.subject,
            description=ticket_data.description
        )

    selected_agent = find_least_busy_agent(database_session)

    if selected_agent is not None:
        assigned_agent_id = selected_agent.id
    else:
        assigned_agent_id = None

    ticket = Ticket(
        customer_id = ticket_data.customer_id,
        description = ticket_data.description,
        priority = final_priority,
        category = predicted_category,
        status = TicketStatus.OPEN.value,
        subject = ticket_data.subject,
        assigned_agent_id=assigned_agent_id
    )


    try:
        database_session.add(ticket)
        database_session.flush()

        automation_job = AIAutomationJob(
              ticket_id=ticket.id,
              status="pending",
              attempt_count=0
            )
        
        database_session.add(automation_job)

        activity = TicketActivity(
            ticket_id=ticket.id,
            action = TicketActivityAction.CREATED.value,
            old_value = None,
            new_value = ticket.status,
            performed_by = "system"
        )

        database_session.add(activity)

        if selected_agent is not None:

            assignment_activity = TicketActivity(
                ticket_id = ticket.id,
                action= TicketActivityAction.ASSIGNED.value,
                old_value = None,
                new_value=str(selected_agent.id),
                performed_by="system"
            )

            database_session.add(assignment_activity)
        
        database_session.commit()

        background_tasks.add_task(
             generate_ai_suggestion_for_ticket,
             ticket.id
        )
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

    if old_agent_id == new_agent_id:
            return ticket
    
    old_agent_id = ticket.assigned_agent_id
    
    ticket.assigned_agent = agent
    ticket.assigned_agent_id = agent.id

    new_agent_id = agent.id

    
    if old_agent_id is None:
        action = TicketActivityAction.ASSIGNED.value
    else:
        action = TicketActivityAction.REASSIGNED.value 

    activity = TicketActivity(
          ticket_id = ticket.id,
          action = action,
          old_value= str(old_agent_id) if old_agent_id is not None else None,
          new_value= str(new_agent_id),
          performed_by = "system"
    )

    database_session.add(activity)

    try:
       database_session.commit()
       database_session.refresh(ticket)
    except SQLAlchemyError:
        database_session.rollback()
        raise

    return ticket

@router.get(
    "/{ticket_id}/activities",
    response_model=list[TicketActivityResponse]
)
def get_activities(
    ticket_id : int = Path(gt=0),
    database_session: Session = Depends(get_db)
):
    statement = select(TicketActivity)

    ticket = database_session.get(Ticket, ticket_id)
    
    if ticket is None:
        raise HTTPException(
            status_code=404,
            detail="Not found"
        )

    statement = statement.where(
        TicketActivity.ticket_id == ticket_id
    )

    statement = statement.order_by(
        TicketActivity.created_at.asc(),
        TicketActivity.id.asc()
    )

    activities = database_session.scalars(statement).all()

    

    return activities

@router.post(
    "/tickets/categorize",
    response_model = TicketCategorizeResponse
)
def find_category(
    message_data: TicketCategorizeRequest
):
    category = categorize_ticket(
        message_data.subject,
        message_data.description
    )

    return TicketCategorizeResponse(
        category=category
    )

@router.post(
    "/tickets/predict-priority",
    response_model = TicketPriorityResponse
)
def preview_ticket_priority(
    message_data: TicketPriorityRequest
):

    result = explain_ticket_priority(
        message_data.subject,
        message_data.description
    )

    return TicketPriorityResponse(
        predicted_priority=result["predicted_priority"],
        matched_keywords=result["matched_keywords"],
        reason=result["reason"]
    )

@router.post(
    "/{ticket_id}/suggest-reply",
    response_model=TicketReplySuggestionResponse
)
def suggest_ticket_reply(
    ticket_id: int,
    database_session: Session = Depends(get_db)
):

    ticket = database_session.get(Ticket, ticket_id)

    if ticket is None:
        raise HTTPException(
            status_code=404,
            detail="Ticket not found"
        )
    statement = (
            select(TicketMessage)
            .where(
                TicketMessage.ticket_id == ticket_id
            )
            .order_by(
                TicketMessage.created_at.asc(),
                TicketMessage.id.asc()
            )
        )
    
    messages = database_session.scalars(statement).all()
    
    con_history = format_conversation_history(messages)

    try:
        suggest_reply = generate_ticket_reply(
            ticket.subject,
            ticket.description,
            conversation_history= con_history
        )

    except Exception:
        raise HTTPException(
            status_code=503,
            detail="AI reply suggestion is temporarily unavailable"
        )

    validate = validate_ai_reply(suggest_reply)

    if validate["is_valid"] == False:
        raise HTTPException(
            status_code=503,
            detail="Invalid response."
        )

    reply_suggestion = AIReplySuggestion(
        ticket_id=ticket.id,
        suggested_reply=suggest_reply,
        status="pending"
    )

    database_session.add(reply_suggestion)

     
    try:
        database_session.commit()
        database_session.refresh(reply_suggestion)
    
    except SQLAlchemyError:

        database_session.rollback()
        raise HTTPException(
            status_code=500,
            detail="Failed to save AI reply suggestion"
        )
    

    return TicketReplySuggestionResponse(
        id=reply_suggestion.id,
        status=reply_suggestion.status,
        ticket_id=ticket.id,
        subject=ticket.subject,
        suggested_reply= reply_suggestion.suggested_reply
    )

@router.get(
    "/{ticket_id}/ai-suggestions",
    response_model=list[AIReplySuggestionListResponse]
)
def get_pending_ai_suggestions(
    ticket_id: int,
    database_session: Session = Depends(get_db)
):

    ticket = database_session.get(Ticket, ticket_id)

    if ticket is None:
        raise HTTPException(
            status_code=404,
            detail="Ticket Not found"
        )

    statement = (
        select(AIReplySuggestion)
        .where(
          AIReplySuggestion.ticket_id == ticket_id,
          AIReplySuggestion.status == "pending"
        ).order_by(
            AIReplySuggestion.created_at.desc(),
             AIReplySuggestion.id.desc()
        ) 
      )

    result = database_session.scalars(statement).all()

    return result

@router.patch(
        "/{suggestion_id}/review",
        response_model=AIReplyReviewResponse
        )

def review_ai_suggestion(
    suggestion_id: int,
    payload: AIReplyReviewRequest,
    database_session: Session = Depends(get_db)
):  
    suggestion = database_session.get(AIReplySuggestion, suggestion_id)

    if suggestion is None:
        raise HTTPException (
            status_code=404,
            detail="Not found"
    )

    if not suggestion.status == "pending":
        raise HTTPException(
            status_code=409,
            detail="Suggestion has already been reviewed"
        )
    
    agent = database_session.get(SupportAgent, payload.agent_id)

    if agent is None:
        raise HTTPException(
            status_code=404,
            detail="Agent not found"
    )

    if not agent.is_active:
        raise HTTPException(
            status_code=403,
            detail="Inactive agents cannot review suggestions"
    )

    if payload.action == "approve":

        suggestion.status = "approved"

        if payload.edited_reply is not None:
            suggestion.edited_reply = payload.edited_reply.strip()

    elif payload.action == "reject":

        if payload.edited_reply is not None:
            raise HTTPException(
                status_code=422,
                detail="Rejected suggestions cannot contain edited replies"
            )

        suggestion.status = "rejected"
        suggestion.edited_reply = None

     
    suggestion.reviewed_by_agent_id = agent.id
    suggestion.reviewed_at = datetime.now(timezone.utc)

     
    try:
        database_session.commit()
        database_session.refresh(suggestion)

    except SQLAlchemyError:
        database_session.rollback()
        raise HTTPException(
            status_code=500,
            detail="Failed to review AI suggestion"
        )

    return AIReplyReviewResponse(
        id=suggestion.id,
        ticket_id=suggestion.ticket_id,
        status=suggestion.status,
        suggested_reply=suggestion.suggested_reply,
        edited_reply=suggestion.edited_reply,
        reviewed_by_agent_id=suggestion.reviewed_by_agent_id,
        reviewed_at=suggestion.reviewed_at
    )
@router.get(
    "/{ticket_id}/ai-automation/jobs",
    response_model=list[AIAutomationJobResponse]
)
def get_ticket_automation_jobs(
    ticket_id: int,
    database_session: Session = Depends(get_db)
):
    ticket = database_session.get(Ticket, ticket_id)

    if ticket is None:
        raise HTTPException(
            status_code=404,
            detail="Not found"
        )
    
    statement = (
        select(AIAutomationJob)
        .where(AIAutomationJob.ticket_id == ticket_id)
        .order_by(
            AIAutomationJob.created_at.desc(),
            AIAutomationJob.id.desc()
        )
    )

    jobs = database_session.scalars(statement).all()

    return jobs



    



    
    