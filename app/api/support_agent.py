from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)

from sqlalchemy import and_, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.support_agent import SupportAgent
from app.models.ticket import Ticket

from app.schemas.support_agent import (
    AgentWorkloadResponse,
    SupportAgentResponse,
    SupportAgentCreate,
    SupportAgentUpdate,
    AgentPasswordResetRequest,
)

from app.db.dependencies import get_db
from app.core.auth_dependencies import require_admin
from app.core.security import hash_password


router = APIRouter(
    prefix="/agents",
    tags=["Agents"],
    dependencies=[Depends(require_admin)],
)


# --------------------------------------------------
# Helper: Retrieve an agent
# --------------------------------------------------

def get_agent_or_404(
    agent_id: int,
    db: Session,
) -> SupportAgent:

    agent = db.get(SupportAgent, agent_id)

    if agent is None:
        raise HTTPException(
            status_code=404,
            detail="Support agent not found",
        )

    return agent


# --------------------------------------------------
# Create basic agent record
# --------------------------------------------------

@router.post(
    "",
    response_model=SupportAgentResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_agent(
    model_data: SupportAgentCreate,
    database_session: Session = Depends(get_db),
):
    email = str(model_data.email).strip().lower()

    existing_agent = database_session.scalar(
        select(SupportAgent).where(
            SupportAgent.email == email
        )
    )

    if existing_agent is not None:
        raise HTTPException(
            status_code=409,
            detail="Agent email already exists",
        )

    agent = SupportAgent(
        name=model_data.name.strip(),
        email=email,
        role="agent",
        is_active=False,
    )

    database_session.add(agent)

    try:
        database_session.commit()
        database_session.refresh(agent)

    except IntegrityError:
        database_session.rollback()

        raise HTTPException(
            status_code=409,
            detail="Agent conflicts with database constraints",
        )

    return agent


# --------------------------------------------------
# Get all agents
# --------------------------------------------------

@router.get(
    "",
    response_model=list[SupportAgentResponse],
)
def get_agent(
    is_active: bool | None = None,
    database_session: Session = Depends(get_db),
):
    statement = select(SupportAgent)

    if is_active is not None:
        statement = statement.where(
            SupportAgent.is_active == is_active
        )

    statement = statement.order_by(
        SupportAgent.id.asc()
    )

    agents = database_session.scalars(
        statement
    ).all()

    return agents


# --------------------------------------------------
# Get agent workload
# Static route must appear before /{agent_id}
# --------------------------------------------------

@router.get(
    "/workload",
    response_model=list[AgentWorkloadResponse],
)
def get_agent_workload(
    database_session: Session = Depends(get_db),
):
    statement = (
        select(
            SupportAgent,
            func.count(Ticket.id).label(
                "active_tickets"
            ),
        )
        .outerjoin(
            Ticket,
            and_(
                Ticket.assigned_agent_id
                == SupportAgent.id,

                Ticket.status.in_(
                    ["open", "in_progress"]
                ),
            ),
        )
        .group_by(SupportAgent.id)
        .order_by(SupportAgent.id.asc())
    )

    results = database_session.execute(
        statement
    ).all()

    workloads = []

    for row in results:

        agent = row.SupportAgent

        workloads.append(
            AgentWorkloadResponse(
                agent_id=agent.id,
                agent_name=agent.name,
                is_active=agent.is_active,
                active_tickets=row.active_tickets,
            )
        )

    return workloads


# --------------------------------------------------
# Get selected agent
# --------------------------------------------------

@router.get(
    "/{agent_id}",
    response_model=SupportAgentResponse,
)
def get_selected_agent(
    agent_id: int,
    database_session: Session = Depends(get_db),
):
    return get_agent_or_404(
        agent_id,
        database_session,
    )


# --------------------------------------------------
# Update agent information
# --------------------------------------------------

@router.put(
    "/{agent_id}",
    response_model=SupportAgentResponse,
)
def update_agent(
    agent_id: int,
    update_data: SupportAgentUpdate,
    database_session: Session = Depends(get_db),
    admin: SupportAgent = Depends(require_admin),
):
    agent = get_agent_or_404(
        agent_id,
        database_session,
    )

    updated_data = update_data.model_dump(
        exclude_unset=True
    )

    for field_name, value in updated_data.items():

        if value is None:
            raise HTTPException(
                status_code=422,
                detail=f"{field_name} cannot be null",
            )

    # Prevent administrator self-deactivation

    if (
        agent.id == admin.id
        and updated_data.get("is_active") is False
    ):
        raise HTTPException(
            status_code=400,
            detail="You cannot deactivate your own account",
        )

    # Prevent activation without a password

    if (
        updated_data.get("is_active") is True
        and not agent.password_hash
    ):
        raise HTTPException(
            status_code=400,
            detail="Set a password before activating this account",
        )

    # Normalize and validate email

    if "email" in updated_data:

        email = str(
            updated_data["email"]
        ).strip().lower()

        duplicate_agent = database_session.scalar(
            select(SupportAgent).where(
                SupportAgent.email == email,
                SupportAgent.id != agent_id,
            )
        )

        if duplicate_agent is not None:
            raise HTTPException(
                status_code=409,
                detail="Agent email already exists",
            )

        updated_data["email"] = email

    if "name" in updated_data:

        name = updated_data["name"].strip()

        if len(name) < 2:
            raise HTTPException(
                status_code=422,
                detail="Name must contain at least 2 characters",
            )

        updated_data["name"] = name

    for field_name, value in updated_data.items():
        setattr(agent, field_name, value)

    try:
        database_session.commit()
        database_session.refresh(agent)

    except IntegrityError:
        database_session.rollback()

        raise HTTPException(
            status_code=409,
            detail="Agent update conflicts with database constraints",
        )

    return agent


# --------------------------------------------------
# Activate agent
# --------------------------------------------------

@router.patch(
    "/{agent_id}/activate",
    response_model=SupportAgentResponse,
)
def activate_agent(
    agent_id: int,
    database_session: Session = Depends(get_db),
):
    agent = get_agent_or_404(
        agent_id,
        database_session,
    )

    if not agent.password_hash:
        raise HTTPException(
            status_code=400,
            detail="Set a password before activating this account",
        )

    if agent.is_active:
        return agent

    agent.is_active = True

    database_session.commit()
    database_session.refresh(agent)

    return agent


# --------------------------------------------------
# Deactivate agent
# --------------------------------------------------

@router.patch(
    "/{agent_id}/deactivate",
    response_model=SupportAgentResponse,
)
def deactivate(
    agent_id: int,
    database_session: Session = Depends(get_db),
    admin: SupportAgent = Depends(require_admin),
):
    agent = get_agent_or_404(
        agent_id,
        database_session,
    )

    if agent.id == admin.id:
        raise HTTPException(
            status_code=400,
            detail="You cannot deactivate your own account",
        )

    if not agent.is_active:
        return agent

    agent.is_active = False

    database_session.commit()
    database_session.refresh(agent)

    return agent


# --------------------------------------------------
# Set or reset agent password
# --------------------------------------------------

@router.patch(
    "/{agent_id}/reset-password",
    response_model=SupportAgentResponse,
)
def reset_agent_password(
    agent_id: int,
    payload: AgentPasswordResetRequest,
    database_session: Session = Depends(get_db),
    admin: SupportAgent = Depends(require_admin),
):
    agent = get_agent_or_404(
        agent_id,
        database_session,
    )

    # Prevent an administrator from taking over
    # another administrator's account through this API.

    if agent.role == "admin" and agent.id != admin.id:
        raise HTTPException(
            status_code=403,
            detail="Cannot reset another administrator's password",
        )

    agent.password_hash = hash_password(
        payload.password
    )

    database_session.commit()
    database_session.refresh(agent)

    return agent