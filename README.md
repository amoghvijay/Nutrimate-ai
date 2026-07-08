<div align="center">

<img src="Logo/Nutrimate_AI_Logo.png" alt="NutriMate AI Logo" width="260"/>

# NutriMate AI

### Your Personal AI Nutrition Research & Action Agent

*Smart insights. Healthier you.*

[![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Claude](https://img.shields.io/badge/Powered%20by-Claude-D97757?style=flat-square)](https://www.anthropic.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](#license)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg?style=flat-square)](#contribution-guidelines)

</div>

---

## Table of Contents

- [Overview](#overview)
- [Why an Agent, Not a Chatbot](#why-an-agent-not-a-chatbot)
- [Features](#features)
- [Architecture](#architecture)
- [Agentic Workflow](#agentic-workflow)
- [Screenshots](#screenshots)
- [Technology Stack](#technology-stack)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Usage Examples](#usage-examples)
- [Security & Privacy](#security--privacy)
- [Roadmap](#roadmap)
- [Contribution Guidelines](#contribution-guidelines)
- [License](#license)
- [Contact](#contact)

---

## Overview

Generic diet advice doesn't work because no two bodies, schedules, or goals are the same. **NutriMate AI** is a full-stack health and nutrition agent that combines a real calorie/macro calculator, persistent food and water logging, and a Claude-powered assistant that doesn't just *talk about* your nutrition — it **acts** on it.

Say "I had two eggs and toast" in the chat, and NutriMate estimates the nutrition and logs it to your diary automatically. Ask "how am I doing today?" and it pulls your actual logged totals before answering — no guessing, no generic advice detached from your real data.

**Built as an industrial training project** to demonstrate a complete, production-shaped AI agent: authentication, a relational data model, tool-calling LLM integration, and a polished frontend, all in one repository.

---

## Why an Agent, Not a Chatbot

| Ordinary Chatbot | NutriMate AI Agent |
|---|---|
| Answers questions in isolation | Grounds every answer in your real logged data |
| Forgets what you tell it | Persists meals, water, and weight to a database |
| You manually log everything | Understands natural language and logs it *for* you |
| Generic advice | Personalized to your BMR/TDEE/macro targets |

This is powered by **Claude's tool-use (function-calling)** — the model decides when an action is needed and calls a real backend function, not a scripted `if/else` chain.

---

## Features

| Category | Capability |
|---|---|
| 🔐 **Secure Auth** | Bcrypt-hashed passwords, token-based sessions |
| 🧬 **Health Calculator** | BMI, BMR, TDEE, and macro targets via the Mifflin-St Jeor formula |
| 🤖 **AI Action Agent** | Claude tool-calling to log meals, water & weight straight from natural chat |
| 🍽️ **AI Meal Planning** | Personalized daily meal plans generated from your saved profile |
| 💡 **Daily AI Tips** | Fresh, evidence-based nutrition tips on every visit |
| 📝 **Manual Logging** | Full food diary and water tracker for when you'd rather type it yourself |
| 📈 **Progress Charts** | Live macro breakdown (Chart.js doughnut) and weight trend line chart |
| 🎨 **Soft, Modern UI** | Glassmorphism design system built to feel calm, not clinical |

---

## Architecture

```mermaid
flowchart TB
    U["User"] --> FE["Frontend<br/>(HTML / CSS / JS + Chart.js)"]
    FE <--> API["FastAPI Backend<br/>(REST API)"]
    API --> AUTH["Auth Layer<br/>(bcrypt + session tokens)"]
    API --> CALC["Health Calculator<br/>(BMI / BMR / TDEE / Macros)"]
    API --> AGENT["AI Agent Layer<br/>(ai_agent.py)"]
    AGENT <--> CLAUDE["Claude API<br/>(Tool-Use / Function Calling)"]
    AGENT --> TOOLS["Agent Tools<br/>log_meal, log_water, log_weight, get_daily_summary"]
    TOOLS --> DB[("SQLite Database<br/>via SQLAlchemy ORM")]
    CALC --> DB
    AUTH --> DB

    style CLAUDE fill:#c8b6ff,stroke:#8fd3c7,color:#2b2d3a
    style AGENT fill:#8fd3c7,stroke:#2b2d3a,color:#2b2d3a
    style DB fill:#ffd6a5,stroke:#2b2d3a,color:#2b2d3a
```

---

## Agentic Workflow

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant Backend as FastAPI
    participant Claude
    participant DB as SQLite

    User->>Frontend: "I ate 2 eggs and toast"
    Frontend->>Backend: POST /api/chat
    Backend->>Claude: messages.create(tools=[log_meal, ...])
    Claude-->>Backend: tool_use: log_meal(food, calories, macros)
    Backend->>DB: INSERT INTO meal_logs
    DB-->>Backend: confirmation
    Backend->>Claude: tool_result
    Claude-->>Backend: natural language reply
    Backend-->>Frontend: reply, history
    Frontend-->>User: "Logged! That's about 220 kcal..."
```

---

## Screenshots

<table>
<tr>
<td width="50%"><img src="screenshots/Log_In_Page.png" alt="Login"/><p align="center"><b>Log In</b></p></td>
<td width="50%"><img src="screenshots/Sign_Up_Page.png" alt="Sign Up"/><p align="center"><b>Sign Up</b></p></td>
</tr>
<tr>
<td width="50%"><img src="screenshots/Dashboard.png" alt="Dashboard"/><p align="center"><b>Dashboard</b></p></td>
<td width="50%"><img src="screenshots/Profile_&_Calculator.png" alt="Profile & Calculator"/><p align="center"><b>Profile & Calculator</b></p></td>
</tr>
<tr>
<td width="50%"><img src="screenshots/AI_Agent_ChatBot.png" alt="AI Agent Chat"/><p align="center"><b>AI Agent Chat</b></p></td>
<td width="50%"><img src="screenshots/AI_Meal_Plan_Generator.png" alt="AI Meal Plan"/><p align="center"><b>AI Meal Plan</b></p></td>
</tr>
<tr>
<td width="50%"><img src="screenshots/Food_&_Water_Loged_Manager.png" alt="Food & Water Log"/><p align="center"><b>Food & Water Log</b></p></td>
<td width="50%"><img src="screenshots/Progress_Graph_Generator.png" alt="Progress"/><p align="center"><b>Progress Charts</b></p></td>
</tr>
</table>

---

## Technology Stack

| Layer | Technology |
|---|---|
| Backend Framework | ![FastAPI](https://img.shields.io/badge/-FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white) |
| Language | ![Python](https://img.shields.io/badge/-Python-3776AB?style=flat-square&logo=python&logoColor=white) |
| ORM / Database | ![SQLAlchemy](https://img.shields.io/badge/-SQLAlchemy-D71F00?style=flat-square) ![SQLite](https://img.shields.io/badge/-SQLite-003B57?style=flat-square&logo=sqlite&logoColor=white) |
| AI Model | ![Anthropic](https://img.shields.io/badge/-Claude%20API-D97757?style=flat-square) |
| Server | ![Uvicorn](https://img.shields.io/badge/-Uvicorn-499848?style=flat-square) |
| Auth | ![bcrypt](https://img.shields.io/badge/-bcrypt-4B32C3?style=flat-square) |
| Frontend | ![HTML5](https://img.shields.io/badge/-HTML5-E34F26?style=flat-square&logo=html5&logoColor=white) ![CSS3](https://img.shields.io/badge/-CSS3-1572B6?style=flat-square&logo=css3&logoColor=white) ![JavaScript](https://img.shields.io/badge/-JavaScript-F7DF1E?style=flat-square&logo=javascript&logoColor=black) |
| Charts | ![Chart.js](https://img.shields.io/badge/-Chart.js-FF6384?style=flat-square&logo=chartdotjs&logoColor=white) |
| Deployment | ![Render](https://img.shields.io/badge/-Render-46E3B7?style=flat-square&logo=render&logoColor=white) |

---

## Project Structure

nutrimate-ai/
├── backend/
│   ├── main.py           # FastAPI app & all REST endpoints
│   ├── ai_agent.py       # Claude tool-use agent + meal plan/tip generation
│   ├── models.py         # SQLAlchemy ORM models
│   ├── database.py       # DB engine/session setup
│   ├── requirements.txt
│   ├── .env.example      # Environment variable template
│   └── Procfile          # For platform deployment (Render/Railway)
├── frontend/
│   └── index.html        # Full single-page UI
├── logo/
│   └── logo.png
├── screenshots/
│   └── *.png
├── .gitignore
└── README.md

---

## Installation

**Prerequisites:** Python 3.10+, an [Anthropic API key](https://console.anthropic.com/)

```bash
# 1. Clone the repository
git clone https://github.com/amoghvijay/Nutrimate-ai.git
cd Nutrimate-ai/backend

# 2. Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment variables
copy .env.example .env       # Windows
# cp .env.example .env       # macOS/Linux
# then edit .env and add your ANTHROPIC_API_KEY

# 5. Run the backend
uvicorn main:app --reload --port 8000
```

Open `frontend/index.html` in your browser (or serve it with VS Code Live Server). The frontend talks to `http://localhost:8000` by default.

---

## Quick Start

```bash
cd backend
venv\Scripts\activate
uvicorn main:app --reload --port 8000
```
Then open `frontend/index.html` → Sign Up → Set up your Profile → try the AI Agent Chat.

---

## Usage Examples

**Natural-language logging:**
> "I just had 2 boiled eggs and a slice of toast"
> → Agent estimates ~220 kcal, 14g protein, and logs it to your diary instantly.

**Grounded feedback:**
> "How am I doing today?"
> → Agent calls `get_daily_summary`, then replies using your *actual* totals — not a guess.

**Personalized planning:**
> Click *Generate Today's Plan* on the Meal Plan tab → returns a full day of meals sized to your saved BMR/TDEE targets.

---

## Security & Privacy

- Passwords are hashed with **bcrypt** — plaintext passwords are never stored.
- API keys live only in environment variables (`.env`), never committed to version control.
- Session tokens are required on every authenticated endpoint.
- The AI is prompted to give general nutrition guidance only, and to recommend professional medical consultation for health concerns — it never diagnoses.

> **Note:** This project uses simple in-memory sessions and SQLite for demonstration purposes. A production deployment would use persistent JWT sessions and a managed database (e.g., PostgreSQL).

---

## Roadmap

```mermaid
timeline
    title NutriMate AI — Future Direction
    Now : Core agent, Calculator, Logging, Charts
    Next : Wearable and fitness tracker sync : Multi-language support
    Later : Voice assistant integration : Persistent cloud database
    Future : Doctor collaboration tools : Real-time health monitoring
```

---

## Contribution Guidelines

Contributions are welcome!

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Commit your changes with clear messages
4. Open a Pull Request describing what you changed and why

Please keep PRs focused — one feature or fix per PR — and follow existing code style (PEP8 for Python).

---

## License

This project is licensed under the **MIT License** — free to use, modify, and distribute with attribution.

---

## Contact

**Amogh Vijay**

[![GitHub](https://img.shields.io/badge/-GitHub-181717?style=flat-square&logo=github&logoColor=white)](https://github.com/amoghvijay)

---

<div align="center">

*Built with care for healthier lives through AI.*

</div>