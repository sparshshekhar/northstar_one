import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from groq import Groq
from models import (
    SiteVisitBooking, BookingResponse,
    ChatRequest, ChatResponse, StartResponse,
    SessionAnalytics, HistoryResponse,
)
from booking_store import attempt_booking
from conversation_store import store
from prompts import SYSTEM_PROMPT
from analytics import generate_analytics, generate_closing_message
from nlp_helpers import detect_language, is_closing_message
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

app = FastAPI()

origins = [
    "https://northstar-one-eight.vercel.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
MODEL = "openai/gpt-oss-120b"

GREETING_TEXT = (
    "Hi! I'm Relo, the AI assistant from Northstar Homes. I'm here to help you with "
    "Northstar One — a residential project in Sector 79, Gurugram, offering 2 BHK and "
    "3 BHK homes starting at \u20b91.35 Cr and \u20b91.75 Cr respectively."
)


def sanitize_reply(text: str) -> str:
    """Hard guardrail: only return text up to and including the first '?'."""
    if not text:
        return text
    text = text.strip()
    q_index = text.find("?")
    if q_index != -1:
        return text[: q_index + 1].strip()
    return text


def build_language_hint(lang: str) -> str:
    """Explicit, script-level instruction per detected language. The system
    prompt already asks the model to mirror language generally, but that
    alone was not reliable enough (it kept drifting into English or full
    Devanagari) — so each turn gets a hard, specific rule plus a short
    example to anchor the exact style expected.
    """
    if lang == "hindi":
        return (
            "\n\nIMPORTANT LANGUAGE RULE: The customer just wrote in Hindi using "
            "Devanagari script. Reply ENTIRELY in Hindi using Devanagari script. "
            "Do not switch to English."
        )
    if lang == "hinglish":
        return (
            "\n\nIMPORTANT LANGUAGE RULE: The customer just wrote in Hinglish — "
            "Hindi and English words mixed together, written in ROMAN/LATIN "
            "letters (not Devanagari). Reply in that exact same style: Roman "
            "letters only, naturally mixing Hindi and English words, the way an "
            "Indian would text a friend. Do NOT reply in pure English. Do NOT "
            "use Devanagari script at all.\n"
            "Example of the style expected: customer says 'kab tak mil sakta hai' "
            "-> you reply something like 'Mujhe abhi exact date nahi pata, lekin "
            "main aapko jald hi confirm kar dunga.'"
        )
    return (
        "\n\nIMPORTANT LANGUAGE RULE: The customer just wrote in English. "
        "Reply entirely in English."
    )


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/start/{session_id}", response_model=StartResponse)
def start_conversation(session_id: str):
    """Seeds the conversation with a static greeting, then asks the model
    for the first real question as a SEPARATE message — so they never
    arrive merged into one bubble."""
    history = store.get_history(session_id)
    if history:
        return StartResponse(session_id=session_id, messages=[])

    store.add_message(session_id, "assistant", GREETING_TEXT)

    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + store.get_history(session_id)
    try:
        completion = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            temperature=0.3,
            max_tokens=300,
            reasoning_effort="low",
        )
        first_question = completion.choices[0].message.content
        if not first_question or not first_question.strip():
            raise ValueError("Empty completion from model")
        first_question = sanitize_reply(first_question).replace("[[END]]", "").strip()
    except Exception as e:
        first_question = "Would you be looking for a 2 BHK or a 3 BHK?"
        print(f"[Groq error] {e}")

    store.add_message(session_id, "assistant", first_question)

    return StartResponse(session_id=session_id, messages=[GREETING_TEXT, first_question])


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Empty message")

    store.add_message(req.session_id, "user", req.message)

    if is_closing_message(req.message):
        lang = detect_language(req.message)
        try:
            reply = generate_closing_message(req.session_id, lang)
        except Exception as e:
            reply = (
                "Thanks so much for your time today. We covered your interest, "
                "budget, and next steps — someone from our team will follow up "
                "if needed. Take care!"
            )
            print(f"[Groq error] {e}")

        store.add_message(req.session_id, "assistant", reply)
        store.set_ended(req.session_id, True)
        return ChatResponse(session_id=req.session_id, reply=reply, conversation_ended=True)

    lang = detect_language(req.message)
    lang_hint = build_language_hint(lang)

    messages = (
        [{"role": "system", "content": SYSTEM_PROMPT + lang_hint}]
        + store.get_history(req.session_id)
    )

    try:
        completion = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            temperature=0.3,
            max_tokens=300,
            reasoning_effort="low",
        )
        reply = completion.choices[0].message.content
        if not reply or not reply.strip():
            raise ValueError("Empty completion from model")
        reply = sanitize_reply(reply)
    except Exception as e:
        reply = (
            "Sorry, I'm having a little trouble right now. "
            "Could you try again in a moment, or I can have someone call you back?"
        )
        print(f"[Groq error] {e}")

    conversation_ended = "[[END]]" in reply
    reply = reply.replace("[[END]]", "").strip()

    store.add_message(req.session_id, "assistant", reply)
    if conversation_ended:
        store.set_ended(req.session_id, True)

    return ChatResponse(session_id=req.session_id, reply=reply, conversation_ended=conversation_ended)


@app.get("/history/{session_id}", response_model=HistoryResponse)
def get_session_history(session_id: str):
    """Kept for completeness/debugging — the frontend no longer calls this
    on load, since every page refresh now starts a brand new session_id
    instead of restoring an old one."""
    history = store.get_history(session_id)
    ended = store.is_ended(session_id)
    return HistoryResponse(session_id=session_id, messages=history, ended=ended)


@app.post("/reset/{session_id}")
def reset_session(session_id: str):
    store.reset(session_id)
    return {"status": "reset", "session_id": session_id}


@app.post("/book-visit", response_model=BookingResponse)
def book_visit(req: SiteVisitBooking):
    return attempt_booking(req)


@app.get("/analytics/{session_id}", response_model=SessionAnalytics)
def analytics(session_id: str):
    return generate_analytics(session_id)