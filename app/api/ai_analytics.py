from app.core.auth_dependencies import require_admin
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, case, and_
from sqlalchemy.orm import Session

from datetime import datetime, timedelta, timezone

from app.db.dependencies import get_db
from app.models.ai_automation_job import AIAutomationJob
from app.schemas.ai_analytics import AIAnalyticsOverviewResponse, AIAutomationTrendResponse, AIReplyAnalyticsResponse, AgentAIAnalyticsResponse
from app.models.ai_reply_suggestion import AIReplySuggestion
from sqlalchemy import and_

from app.models.support_agent import SupportAgent
from app.models.ai_reply_suggestion import AIReplySuggestion

router = APIRouter(
    dependencies=[Depends(require_admin)],
    prefix="/ai-analytics",
    tags=["AI Analytics"]
)

@router.get(
    "/overview",
    response_model=AIAnalyticsOverviewResponse
)
def get_ai_analytics_overview(
    database_session: Session = Depends(get_db)
):
    statement = select(
    func.count(AIAutomationJob.id).label("total_jobs"),

    func.sum(
        case(
            (AIAutomationJob.status == "completed", 1),
            else_=0
        )
    ).label("completed_jobs"),
    func.sum(
        case(
            (AIAutomationJob.status == "pending", 1),
            else_=0
        )
    ).label("pending_jobs"),
    func.sum(
        case(
            (AIAutomationJob.status == "processing", 1),
            else_=0
        )
    ).label("processing_jobs"),
    func.sum(
        case(
            (AIAutomationJob.status == "failed", 1),
            else_=0
        )
    ).label("failed_jobs"),
        func.coalesce(
        func.sum(AIAutomationJob.attempt_count),
        0
    ).label("total_attempts")

)
    result = database_session.execute(statement).one()

    total_jobs = result.total_jobs
    completed_jobs = result.completed_jobs or 0
    processing_jobs = result.processing_jobs or 0
    failed_jobs = result.failed_jobs or 0
    pending_jobs = result.pending_jobs or 0
    total_attempts = result.total_attempts


    success_rate = (
        (completed_jobs / total_jobs) * 100
        if total_jobs > 0
        else 0.0
    )

    success_rate = round(success_rate, 2)

    return AIAnalyticsOverviewResponse(
        total_jobs = total_jobs,
        pending_jobs = pending_jobs,
        processing_jobs = processing_jobs,
        completed_jobs = completed_jobs,
        failed_jobs = failed_jobs,
        success_rate = success_rate,
        total_attempts = total_attempts
    )

@router.get(
    "/replies",
    response_model=AIReplyAnalyticsResponse
)
def get_ai_reply_analytics(
    database_session: Session = Depends(get_db)
):
    statement = select(

    func.count(
        AIReplySuggestion.id
    ).label("total_suggestions"),

    func.sum(
        case(
            (AIReplySuggestion.status == "approved", 1),
            else_=0
        )
    ).label("approved_suggestions"),

    func.sum(
            case(
                (AIReplySuggestion.status == "pending", 1),
                else_=0
            )
    ).label("pending_suggestions"),

    func.sum(
            case(
                (AIReplySuggestion.status == "rejected", 1),
                else_=0
            )
    ).label("rejected_suggestions"),

    
    func.coalesce(
        func.sum(
            case(
                (AIReplySuggestion.status == "sent", 1),
                else_=0
            )
        ),
        0
    ).label("sent_suggestions"),


   
    func.sum(
        case(
            (
                (AIReplySuggestion.edited_reply.is_not(None))
                & (func.trim(AIReplySuggestion.edited_reply) != ""),
                1
            ),
            else_=0
        )
    ).label("edited_suggestions")
    )
    result = database_session.execute(statement).one()
  
    approved_suggestions = result.approved_suggestions
    sent_suggestions = result.sent_suggestions
    rejected_suggestions = result.rejected_suggestions
    total_suggestions = result.total_suggestions


    accepted_suggestions = (
        approved_suggestions + sent_suggestions
    )

    reviewed_suggestions = (
        accepted_suggestions + rejected_suggestions
    )

    approval_rate = (
        round((accepted_suggestions / reviewed_suggestions) * 100, 2)
        if reviewed_suggestions > 0
        else 0.0
    )

    rejection_rate = (
        round((rejected_suggestions / reviewed_suggestions) * 100, 2)
        if reviewed_suggestions > 0
        else 0.0
    )

    send_rate = (
        round((sent_suggestions / total_suggestions) * 100, 2)
        if total_suggestions > 0
        else 0.0
    )

    return AIReplyAnalyticsResponse(
        total_suggestions=total_suggestions,
        pending_suggestions=result.pending_suggestions,
        approved_suggestions=approved_suggestions,
        rejected_suggestions=rejected_suggestions,
        sent_suggestions=sent_suggestions,
        edited_suggestions=result.edited_suggestions,
        approval_rate=approval_rate,
        rejection_rate=rejection_rate,
        send_rate=send_rate
    )

@router.get(
    "/agents",
    response_model=list[AgentAIAnalyticsResponse]
)
def get_agent_ai_analytics(
    database_session: Session = Depends(get_db)
):
    statement = (
            select(
                SupportAgent.id.label("agent_id"),
                SupportAgent.name.label("agent_name"),
                SupportAgent.is_active,

                func.count(
                    AIReplySuggestion.id
                ).label("reviewed_suggestions"),

                func.sum(
                    case(
                        (AIReplySuggestion.status == "approved", 1),
                        else_=0
                    )
                ).label("approved_suggestions"),

                func.sum(
                    case(
                        (AIReplySuggestion.status == "rejected", 1),
                        else_=0
                    )
                ).label("rejected_suggestions"),

                func.sum(
                    case(
                        (AIReplySuggestion.status == "sent", 1),
                        else_=0
                    )
                ).label("sent_suggestions"),

                func.sum(
                    case(
                        (
                            and_(
                                AIReplySuggestion.edited_reply.is_not(None),
                                func.trim(AIReplySuggestion.edited_reply) != ""
                            ),
                            1
                        ),
                        else_=0
                    )
                ).label("edited_suggestions")
            )
            .outerjoin(
                AIReplySuggestion,
                and_(
                    AIReplySuggestion.reviewed_by_agent_id == SupportAgent.id,
                    AIReplySuggestion.status.in_(
                        ["approved", "rejected", "sent"]
                    )
                )
            )
            .group_by(
                SupportAgent.id,
                SupportAgent.name,
                SupportAgent.is_active
            )
            .order_by(SupportAgent.id.asc())
        )

    results = database_session.execute(statement).all()

    analytics = []

    for row in results:
        reviewed = row.reviewed_suggestions
        approved = row.approved_suggestions or 0
        rejected = row.rejected_suggestions or 0
        sent = row.sent_suggestions or 0
        edited = row.edited_suggestions or 0

        acceptance_rate = (
            round(((approved + sent) / reviewed) * 100, 2)
            if reviewed > 0
            else 0.0
        )


        analytic= AgentAIAnalyticsResponse(
            agent_id= row.agent_id,
            agent_name=row.agent_name,
            is_active = row.is_active,
            reviewed_suggestions=reviewed,
            approved_suggestions=approved,
            rejected_suggestions=rejected,
            sent_suggestions=sent,
            edited_suggestions=edited,
            acceptance_rate=acceptance_rate
        )

        analytics.append(analytic)


    return analytics

@router.get(
    "/trends",
    response_model=list[AIAutomationTrendResponse]
)
def get_ai_automation_trends(
    days: int = Query(default=7, ge=1, le=30),
    database_session: Session = Depends(get_db)
):
    now = datetime.now(timezone.utc)

    start_date = (
        now - timedelta(days=days - 1)
    ).date()

    start_datetime = datetime.combine(
        start_date,
        datetime.min.time(),
        tzinfo=timezone.utc
    )
    end_datetime = datetime.combine(
        now.date() + timedelta(days=1),
        datetime.min.time(),
        tzinfo=timezone.utc
    )

    job_date = func.date(
    func.timezone("UTC", AIAutomationJob.created_at)
    )

    statement = (
        select(
            job_date.label("date"),

            func.count(
                AIAutomationJob.id
            ).label("total_jobs"),

            func.sum(
                case(
                    (AIAutomationJob.status == "completed", 1),
                    else_=0
                )
            ).label("completed_jobs"),

            func.sum(
                case(
                    (AIAutomationJob.status == "failed", 1),
                    else_=0
                )
            ).label("failed_jobs")
        )
        .where(
            AIAutomationJob.created_at >= start_datetime,
             AIAutomationJob.created_at < end_datetime
        )
        .group_by(job_date)
        .order_by(job_date.asc())
    )

    results = database_session.execute(statement).all()

    daily_trends = []

    for row in results:
        completed = row.completed_jobs or 0
        total = row.total_jobs
        failed = row.failed_jobs or 0

        daily_success_rate = (
            round((completed/total) * 100,2)
                    if total > 0 
                    else 0.0
            )

        res = AIAutomationTrendResponse(
            date=row.date,
            total_jobs = total,
            completed_jobs=completed,
            failed_jobs=failed,
            success_rate=daily_success_rate
        )

        daily_trends.append(res)

    return daily_trends
