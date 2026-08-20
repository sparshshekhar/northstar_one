import os
import json
from dotenv import load_dotenv
from groq import Groq
from models import SessionAnalytics
from booking_store import get_booking
from conversation_store import store

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))
MODEL = "openai/gpt-oss-120b"

ANALYTICS_PROMPT = """You are analyzing a real-estate sales chatbot conversation.
Read the conversation and produce ONLY a JSON object with these exact keys:
- lead_summary: 1-2 sentence plain-English summary of what the customer wanted
- interested_configuration: "2 BHK", "3 BHK", or null if unclear
- budget_mentioned: the budget as stated by the customer, or null
- lead_quality: "hot" (asked to book/gave contact info/urgent), "warm" (asked real questions, engaged), or "cold" (vague/browsing)

Return ONLY the JSON object, no markdown, no explanation."""


def generate_analytics(session_id: str) -> SessionAnalytics:
    history = store.get_history(session_id)
    booking = get_booking(session_id)

    convo_text = "\n".join(f"{m['role']}: {m['content']}" for m in history)

    completion = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": ANALYTICS_PROMPT},
            {"role": "user", "content": convo_text},
        ],
        temperature=0,
    )

    raw = completion.choices[0].message.content.strip()
    raw = raw.replace("```json", "").replace("```", "").strip()

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        parsed = {
            "lead_summary": "Could not parse lead summary.",
            "interested_configuration": None,
            "budget_mentioned": None,
            "lead_quality": "cold",
        }

    site_visit_status = booking.status if booking else "not_requested"

    return SessionAnalytics(
        session_id=session_id,
        lead_summary=parsed.get("lead_summary", ""),
        interested_configuration=parsed.get("interested_configuration"),
        budget_mentioned=parsed.get("budget_mentioned"),
        site_visit_status=site_visit_status,
        lead_quality=parsed.get("lead_quality", "cold"),
    )