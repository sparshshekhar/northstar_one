import os
import json
from dotenv import load_dotenv
from groq import Groq
from models import SessionAnalytics
from booking_store import get_booking
from conversation_store import store

load_dotenv()

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
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

CLOSING_SUMMARY_PROMPT = """You are Relo, the Northstar One sales assistant. The customer just said thank you / bye, so this conversation is ending now.

Write your FINAL message DIRECTLY to the customer, speaking to them as "you" (or "aap" if replying in Hindi/Hinglish) — never write about them in third person like a report, and never start with words like "Customer" or "The customer".

Your message must have exactly this shape, each part on its own short line:
1. One short line recapping what they were interested in (configuration/budget, if mentioned)
2. One short line on the outcome (e.g. site visit booked for [day/time], or follow-up needed, or just browsing)
3. One short warm thank-you / sign-off line

Keep the whole thing under 40 words total. No markdown, no bullets, no numbering, no headers, no labels like "Line 1:". Just the plain lines, separated by line breaks, spoken as if you're saying goodbye to them directly. Nothing else — no preamble, no explanation, do not restate these instructions."""

LANG_LABEL = {
    "hindi": "Hindi (Devanagari script)",
    "hinglish": "Hinglish (Latin script, mixed Hindi-English)",
    "english": "English",
}


def generate_closing_message(session_id: str, lang: str) -> str:
    history = store.get_history(session_id)
    convo_text = "\n".join(f"{m['role']}: {m['content']}" for m in history)

    lang_label = LANG_LABEL.get(lang, "English")

    system_msg = (
        CLOSING_SUMMARY_PROMPT
        + f"\n\nThe customer's messages were in {lang_label}. "
        + "Write your ENTIRE message in that same language and script — do not default to English."
    )

    completion = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user", "content": convo_text},
        ],
        temperature=0.3,
        max_tokens=400,
        reasoning_effort="low",
    )
    content = completion.choices[0].message.content
    if not content or not content.strip():
        return (
            "Thanks so much for your time today! We've noted everything you shared, "
            "and our team will follow up if needed. Take care!"
        )
    return content.strip()