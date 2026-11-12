
from fastapi import (
    APIRouter, 
    Depends,
    HTTPException, 
    status
)

from sqlalchemy.exc import IntegrityError
from sqlalchemy import select

from app.models.support_agent import SupportAgent
from app.schemas.support_agent import (
    SupportAgentResponse,
    SupportAgentCreate,
    SupportAgentBase
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
    "/{agent}    response_model= SupportAgentResponse
)
def get_agent


@router.get(

)
@router.put(

)
@router.patch(

)