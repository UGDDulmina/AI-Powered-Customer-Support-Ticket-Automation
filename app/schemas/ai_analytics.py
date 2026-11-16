from openai import BaseModel
from datetime import date

class AIAnalyticsOverviewResponse(BaseModel):
    total_jobs: int
    pending_jobs: int
    processing_jobs: int
    completed_jobs: int
    failed_jobs: int
    success_rate: float
    total_attempts: int

class AIReplyAnalyticsResponse(BaseModel):
    total_suggestions: int
    pending_suggestions:int
    approved_suggestions:int
    rejected_suggestions:int
    sent_suggestions:int
    edited_suggestions:int
    approval_rate:float
    rejection_rate:float
    send_rate:float

class AgentAIAnalyticsResponse(BaseModel):
    agent_id: int
    agent_name: str
    is_active: bool
    reviewed_suggestions:int
    approved_suggestions:int
    rejected_suggestions:int
    sent_suggestions:int
    edited_suggestions:int
    acceptance_rate:float

class AIAutomationTrendResponse(BaseModel):
    date: date
    total_jobs: int
    completed_jobs: int
    failed_jobs: int
    success_rate: float
    