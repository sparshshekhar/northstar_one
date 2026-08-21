# Northstar One — AI Sales Agent

An AI-powered conversational sales agent for **Northstar Homes**, built for the Huvo AI Forward Deployed Engineer assignment. The agent qualifies leads, answers questions, handles objections, books site visits, and generates post-conversation analytics — in English, Hindi, and Hinglish.

**Live demo:** https://northstar-one-eight.vercel.app/

## Tech Stack
- **Backend:** FastAPI (Python)
- **LLM:** Groq API (`openai/gpt-oss-120b`)
- **Frontend:** HTML/CSS/JS — Northstar One landing page + embedded chat widget

## Project Structure
```
northstar-one/
├── backend/
│   ├── main.py               # FastAPI app, routes
│   ├── prompts.py            # System prompt
│   ├── models.py             # Pydantic schemas
│   ├── conversation_store.py # In-memory session/message store
│   ├── booking_store.py      # Site-visit booking simulation
│   ├── analytics.py          # Post-conversation analytics generation
│   ├── nlp_helpers.py        # Language detection / message parsing helpers
│   └── requirements.txt
├── frontend/
│   ├── index.html            # Northstar One landing page
│   ├── styles.css
│   └── chatbot.js            # Chat widget — auto-opens 5s after load
├── tests/
│   └── test_cases.md         # Input / expected / actual output
└── README.md
```

## How to Run

1. Clone the repo and go into the backend folder:
   ```
   cd backend
   python -m venv venv
   source venv/bin/activate      # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```
2. Create a `.env` file inside `backend/` and add your own Groq API key:
   ```
   GROQ_API_KEY=your_key_here
   ```
   Get a free key at `console.groq.com`.
3. Start the backend:
   ```
   uvicorn main:app --reload
   ```
4. Open `frontend/index.html` in a browser (or serve it with any static server). The chatbot opens automatically 5 seconds after the page loads.

## Deployment
Live at https://northstar-one-eight.vercel.app/ — frontend on Vercel, backend on Render.

## Key Assumptions
- LLM provider is Groq (free tier) rather than a paid API, chosen to keep the assignment reproducible without billing setup.
- Site-visit availability is simulated via a fixed set of blocked slots (not a real calendar integration), as the assignment scope is a "simple bot."
- Conversation history and bookings are stored in-memory per session — acceptable for a demo/assignment, not production-persistent.
- Analytics are generated at the end of a conversation from the full message history, not in real time per turn.

## Known Limitations
- No persistent database — restarting the backend clears all sessions and bookings.
- Language detection relies on the LLM's own judgment (plus lightweight helper logic) rather than a dedicated language-detection library, so edge cases in mixed-script input may occasionally be misread.
- No authentication/rate-limiting on the API endpoints — fine for a demo, not deployment-hardened.
- Voice interaction itself (speech-to-text/text-to-speech) is not implemented; the prompt is designed to be voice-compatible, but this build is text-only per the assignment's Part 2 scope.

## AI Tools Used
Built iteratively with Claude (Anthropic) — used for system prompt design, FastAPI backend structure, and debugging (e.g., resolving a Groq model deprecation issue during development).
