
from fastapi import (
    APIRouter, 
    Depends,
    HTTPException, 
    status
)

from sqlalchemy.exc import IntegrityError
from sqlalchemy import and_, func, select

from app.models.support_agent import SupportAgent
from app.models.ticket import Ticket
from app.schemas.support_agent import (
    AgentWorkloadResponse,
    SupportAgentResponse,
    SupportAgentCreate,
    SupportAgentUpdate
)

from sqlalchemy.orm import Session

from app.db.dependencies import get_db

router = APIRouter(
    prefix= "/agents",
    tags=["Agents"]
)

@router.post(
    "",
    response_model = SupportAgentResponse,
    status_code=status.HTTP_201_CREATED 
)
def create_agent(
    model_data: SupportAgentCreate,
    database_session: Session = Depends(get_db)
):
    statement = select(SupportAgent).where(
        SupportAgent.email == model_data.email
    )

    email_verify = database_session.scalars(statement)

    if email_verify is not None:
        raise HTTPException(
            status_code=409,
            detail="Email already exits"
        )
    agent = SupportAgent(
       name = model_data.name,
       email = model_data.email
    )

    database_session.add(agent)

    try:
        database_session.commit()
        database_session.refresh(agent)

    except IntegrityError:
        database_session.rollback()

        raise HTTPException(
            status_code=409,
            detail="Agent conflicts with database constraint"
        )

    return agent
    
@router.get(
    "",
    response_model= list[SupportAgentResponse]
)
def get_agent(
    is_active: bool | None=None,
    database_session: Session = Depends(get_db)
):
    statement = select(SupportAgent)

    if is_active is not None:
        statement = statement.where(
            SupportAgent.is_active == is_active
        )

    agents = database_session.scalars(statement).all()

    return agents


@router.get(
    "/{agent_id}",
    response_model= SupportAgentResponse
)
def get_selected_agent(
    agent_id: int,
    database_session: Session = Depends(get_db)
):
    statement = select(SupportAgent)

    statement = statement.where(
        SupportAgent.id == agent_id
    )

    agent = database_session.scalar(statement)

    if agent is None:
        raise HTTPException(
            status_code=404,
            detail="Support agent not found"
        )

    return agent

@router.put(
    "/{agent_id}",
    response_model= SupportAgentResponse
)
def update_agent(
    agent_id: int,
    update_data: SupportAgentUpdate,
    database_session: Session = Depends(get_db)
):
    agent = database_session.get(SupportAgent, agent_id)

    if agent is None:
        raise HTTPException(
            status_code=404,
            detail="agent not found"
        )

    if update_data.email is not None:
        statement = select(SupportAgent).where(
           SupportAgent.email == update_data.email,
           SupportAgent.id != agent_id
        )

        dup_agent = database_session.scalar(statement)

        if dup_agent:
            raise HTTPException(
                status_code=409,
                detail="Duplicate email found."
            )

    updated_agent = update_data.model_dump(
        exclude_unset=True
    )

    for field_name,value in updated_agent.items():
        if value is None:
            raise HTTPException(
                status_code=422,
                detail=f"{field_name} cannot be null"
            )
        setattr(agent, field_name, value)

    try:
        database_session.commit()
        database_session.refresh(agent)

    except IntegrityError:
        database_session.rollback()
        raise HTTPException(
            status_code=409,
            detail="Agent update conflict with database constraints"
        )
    return agent

    
    
@router.patch(
  "/{agent_id}/deactivate",
   response_model= SupportAgentResponse
)
def deactivate(
    agent_id:int,
    database_session: Session = Depends(get_db)
):
   agent = database_session.get(SupportAgent, agent_id)

   if agent is None:
       raise HTTPException(
           status_code=404,
           detail="Not found"
       )

   if not agent.is_active:
       return agent

   agent.is_active = False

   database_session.commit()
   database_session.refresh(agent)

   return agent

@router.get(
    "/workload",
    response_model=list[AgentWorkloadResponse]
)

def get_agent_workload(
    database_session: Session = Depends(get_db)
):
    statement = (
        select(
            SupportAgent,
            func.count(Ticket.id).label("active_tickets")
        ).outerjoin(
            Ticket,
            and_(
                Ticket.assigned_agent_id == SupportAgent.id,
                Ticket.status.in_(["open", "in_progress"])
            )
        ).group_by(SupportAgent.id).order_by(SupportAgent.id.asc())
    )

    results = database_session.execute(statement).all()

    workloads = []

    for row in results:
        agent = row.SupportAgent

        res = AgentWorkloadResponse(
            agent_id=agent.id,
            agent_name=agent.name,
            is_active=agent.is_active,
            active_tickets=row.active_tickets
        )

        workloads.append(res)

    return workloads
