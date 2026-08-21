from pydantic import BaseModel
from typing import Literal

class ChatRequest(BaseModel):
    session_id: str
    message: str

class ChatResponse(BaseModel):
    session_id: str
    reply: str
    conversation_ended: bool = False

class SiteVisitBooking(BaseModel):
    session_id: str
    configuration: Literal["2 BHK", "3 BHK"]
    preferred_date: str
    preferred_time: str
    contact_number: str

class AnalyticsResponse(BaseModel):
    session_id: str
    budget: str | None = None
    configuration: str | None = None
    interest_level: Literal["high", "medium", "low", "not_interested"] | None = None
    site_visit_status: Literal["booked", "failed", "not_requested"] = "not_requested"
    follow_up_required: bool = False
    opted_out: bool = False
    summary: str | None = None


class BookingResponse(BaseModel):
    session_id: str
    status: Literal["confirmed", "failed"]
    message: str
    alternate_suggestion: str | None = None

class SessionAnalytics(BaseModel):
    session_id: str
    lead_summary: str
    interested_configuration: str | None = None
    budget_mentioned: str | None = None
    site_visit_status: Literal["confirmed", "failed", "not_requested"]
    lead_quality: Literal["hot", "warm", "cold"]

class StartResponse(BaseModel):
    session_id: str
    messages: list[str]

class HistoryResponse(BaseModel):
    session_id: str
    messages: list[dict]
    ended: bool