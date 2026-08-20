import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from groq import Groq
from models import SiteVisitBooking, BookingResponse
from booking_store import attempt_booking
from models import ChatRequest, ChatResponse
from conversation_store import store
from prompts import SYSTEM_PROMPT
from models import SessionAnalytics
from analytics import generate_analytics

load_dotenv()

app = FastAPI(title="Northstar One - AI Sales Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten before real deploy
    allow_methods=["*"],
    allow_headers=["*"],
)

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
MODEL = "openai/gpt-oss-120b"

def sanitize_reply(text: str) -> str:
    """
    Hard guardrail: only return text up to and including the first '?'.
    This enforces "ask one question, then stop" at the code level —
    it doesn't matter what the model generates after that point,
    it never reaches the user.
    """
    if not text:
        return text
    text = text.strip()
    q_index = text.find("?")
    if q_index != -1:
        return text[: q_index + 1].strip()
    return text


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Empty message")

    # 1. Log the user's message into this session's history
    store.add_message(req.session_id, "user", req.message)

    # 2. Build the full message list: system prompt + entire running history
    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + store.get_history(req.session_id)

    # 3. Call Groq
    try:
        completion = client.chat.completions.create(
    model=MODEL,
    messages=messages,
    temperature=0.3,
    max_tokens=200,
    reasoning_effort="low",
    stop=["\nCustomer:", "\nUser:", "\nRelo:", "I'm sorry, I'm not interested"],
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

    # 4. Log the assistant's reply into history too, so context persists
    store.add_message(req.session_id, "assistant", reply)

    return ChatResponse(session_id=req.session_id, reply=reply)


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