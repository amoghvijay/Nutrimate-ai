# NutriMate AI — Health & Nutrition Research and Action Agent

An AI agent (not just a chatbot) that **researches and acts**: it chats naturally, but
also autonomously logs meals, water and weight into a real database using Claude's
tool-use (function-calling), on top of a full health-tracking web app.

## Features
- Secure signup/login (bcrypt-hashed passwords, session tokens)
- Profile system with BMI, BMR, TDEE and macro-target calculator (Mifflin-St Jeor formula)
- **AI Action Agent** — a Claude-powered chat that can *do things*: say "I ate 2 eggs and
  toast" and it estimates nutrition and logs it for you automatically; mention your weight
  or water intake and it logs those too. It also fetches your real daily totals before
  giving feedback, so advice is grounded in your actual data.
- AI-generated personalized daily meal plans
- AI-generated rotating daily health tips
- Manual meal & water logging with a live food diary
- Weight-trend and macro-breakdown charts (Chart.js)
- Soft, glassmorphism, mobile-responsive UI designed to feel calm and encouraging

## Tech Stack
- **Backend:** Python, FastAPI, SQLAlchemy, SQLite, Anthropic Claude API (tool use)
- **Frontend:** Single-page HTML/CSS/JS (no build step needed), Chart.js
- **Auth:** Passlib (bcrypt) + simple token sessions

## Project Structure
```
nutrimate-ai/
├── backend/
│   ├── main.py          # FastAPI app & all REST endpoints
│   ├── ai_agent.py       # Claude tool-use agent logic + meal plan/tip generation
│   ├── models.py         # SQLAlchemy ORM models
│   ├── database.py       # DB engine/session setup
│   ├── requirements.txt
│   └── .env              # Add your ANTHROPIC_API_KEY here
└── frontend/
    └── index.html         # Full UI (open directly in a browser)
```

## Setup & Run

### 1. Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
```
Edit `.env` and paste your Anthropic API key:
```
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxxxxxxxxx
```
Then start the server:
```bash
uvicorn main:app --reload --port 8000
```
API docs available at `http://localhost:8000/docs`.

### 2. Frontend
Just open `frontend/index.html` in your browser (double-click it, or use VS Code
"Live Server"). It talks to the backend at `http://localhost:8000`.

## How the "Agent" Part Works
`ai_agent.py` defines Claude tools (`log_meal`, `log_water`, `log_weight`,
`get_daily_summary`). When you chat, Claude decides on its own whether a tool call is
needed, the backend executes it against the real database, feeds the result back to
Claude, and Claude replies conversationally — a genuine agentic loop, not a scripted
if/else chatbot.

## Notes for Evaluation
- Sessions are stored in-memory for simplicity (fine for a training project/demo);
  swap for JWT + Redis for production.
- Nutrition estimates from the AI are approximate, like any nutrition-estimation tool —
  the app always encourages professional medical advice for health concerns.
- Default AI model: `claude-sonnet-4-6` (edit `MODEL` in `ai_agent.py` to change).
