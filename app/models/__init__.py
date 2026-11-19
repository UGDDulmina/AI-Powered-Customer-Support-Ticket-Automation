from app.models.customer import Customer
from app.models.ticket import Ticket
from app.models.ticket_activity import TicketActivity
from app.models.ticket_message import TicketMessage
from app.models.support_agent import SupportAgent
from app.models.ai_automation_job import AIAutomationJob
from app.models.ai_reply_suggestion import AIReplySuggestion

__all__ = [
    "Customer",
    "Ticket",
    "TicketMessage",
    "SupportAgent",
    "TicketActivity",
    "AIAutomationJob",
    "AIReplySuggestion"
]