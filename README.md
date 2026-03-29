# NextHire.AI — AI-Powered Resume-Aware Mock Interview Platform
 
> Simulate real technical interviews with contextual intelligence, persistent memory, structured evaluation, and resume-aware questioning — powered by Google Gemini and built on a production-grade FastAPI + PostgreSQL backend.
 
🔗 **Live Demo:** [https://nexthire-ai-interview-platform.onrender.com](https://nexthire-ai-interview-platform.onrender.com)  
📁 **Repository:** [github.com/harshraj0049/nexthire-ai-interview-platform](https://github.com/harshraj0049/nexthire-ai-interview-platform)
 
---
 
## Table of Contents
 
- [Why NextHire.AI?](#why-nexthireai)
- [Platform Screenshots](#platform-screenshots)
- [Interview Types Supported](#interview-types-supported)
- [System Architecture](#system-architecture)
- [Core Features (Technical Deep-Dive)](#core-features-technical-deep-dive)
  - [Resume Context Injection](#1-resume-context-injection)
  - [Multi-Turn AI Interview Engine](#2-multi-turn-ai-interview-engine)
  - [Coding Round Simulation](#3-coding-round-simulation)
  - [Structured Evaluation Engine](#4-structured-evaluation-engine)
  - [Interview History & Dashboard](#5-interview-history--dashboard)
  - [Authentication & Security](#6-authentication--security)
- [Database Design](#database-design)
- [Infrastructure & Reliability](#infrastructure--reliability)
  - [Rate Limiting](#rate-limiting)
  - [Cron Job — Conversation Cleanup](#cron-job--conversation-cleanup)
  - [Logging & Observability](#logging--observability)
- [Project Structure](#project-structure)
- [Local Setup](#local-setup)
- [Environment Variables](#environment-variables)
- [API Reference](#api-reference)
- [Design Decisions & Engineering Tradeoffs](#design-decisions--engineering-tradeoffs)
- [Roadmap](#roadmap)
- [Author](#author)
 
---
 
## Why NextHire.AI?
 
Most mock interview tools are glorified Q&A chatbots. NextHire.AI is different.
 
It is a **full-stack, production-grade interview simulation system** that replicates the way a real interviewer thinks and behaves — it reads your resume, adapts its questions to your background, holds a multi-turn conversation with full memory, challenges your code without giving away answers, and finally evaluates your entire performance against a structured rubric.
 
| Feature | Typical Mock Tool | NextHire.AI |
|---|---|---|
| Resume-aware questions | ❌ | ✅ LLM reads your actual resume |
| Multi-turn memory | ❌ | ✅ Full conversation persisted in DB |
| Coding round with code review | ❌ | ✅ Live IDE + LLM code feedback |
| Structured evaluation (JSON) | ❌ | ✅ Score, strengths, weaknesses, verdict |
| Interview history & replay | ❌ | ✅ Persistent per-user history |
| Production backend | ❌ | ✅ FastAPI + PostgreSQL + JWT + Rate Limiting |
| 8 interview domains | ❌ | ✅ DSA, System Design, HR, DS, PM, DevOps, BA, SQL |
 
---
 
## Platform Screenshots
 
> **Landing Page**
><img src="./app/static/images/landing.png">
 
> **User Dashboard** 
><img src="./app/static/images/dashborad.png">
 
> **Live Interview Screen** — multi-turn conversation in progress
><img src="./app/static/images/interview_ui.png">
  
**Evaluation Popup** — score, strengths, weaknesses, improvements, final verdict

<table>
  <tr>
    <td><img src="./app/static/images/eval_1.png" width="400"></td>
    <td><img src="./app/static/images/eval_2.png" width="400"></td>
  </tr>
</table>
 
> **Interview History Dashboard** — list of past interviews with scores  
><img src="./app/static/images/history.png">
 
> **Resume Upload**  
><img src="./app/static/images/resume_upload.png">
 
---
 
## Interview Types Supported

NextHire.AI supports **8 distinct interview domains**, each with a customized LLM prompt persona and question strategy:

| # | Domain | Type |
|---|---|---|
| 1 | **DSA / Coding** | Technical |
| 2 | **System Design** | Technical |
| 3 | **HR / Behavioral** | Non-Technical |
| 4 | **Data Science** | Technical |
| 5 | **Product Manager** | Non-Technical |
| 6 | **DevOps** | Technical |
| 7 | **Business Analytics** | Non-Technical |
| 8 | **SQL Developer** | Technical |

---
 
## System Architecture
 
```
┌─────────────────────────────────────────────────────────┐
│                        CLIENT                           │
│     Jinja2 Templates + CodeMirror + Speech-to-Text      │
└───────────────────────────┬─────────────────────────────┘
                            │ HTTP (JWT via HttpOnly Cookie)
┌───────────────────────────▼─────────────────────────────┐
│                    FastAPI Backend                       │
│                                                         │
│  ┌──────────┐  ┌────────────┐  ┌─────────────────────┐  │
│  │   Auth   │  │  Interview │  │   LLM Service Layer │  │
│  │  Router  │  │   Router   │  │  (Prompt Builder +  │  │
│  └──────────┘  └────────────┘  │   Gemini API Call)  │  │
│                                └─────────────────────┘  │
│  ┌──────────────────────┐  ┌──────────────────────────┐  │
│  │   Rate Limiter       │  │  Cron Job Scheduler      │  │
│  │ (per-route, per-IP)  │  │  (conversation cleanup)  │  │
│  └──────────────────────┘  └──────────────────────────┘  │
└───────────────────────────┬─────────────────────────────┘
                            │ SQLAlchemy ORM
┌───────────────────────────▼─────────────────────────────┐
│                    PostgreSQL Database                   │
│   User │ Interview │ InterviewTurn │ InterviewEvaluation │
└─────────────────────────────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────┐
│               Google Gemini API                         │
│   (Resume Summarization, Question Generation,           │
│    Code Feedback, Final Evaluation)                     │
└─────────────────────────────────────────────────────────┘
```
 
**Tech Stack:**
 
| Layer | Technology |
|---|---|
| Backend Framework | FastAPI |
| ORM | SQLAlchemy |
| Database | PostgreSQL |
| LLM | Google Gemini API |
| Auth | JWT + HttpOnly Cookies |
| Frontend | Jinja2 + CodeMirror + Web Speech API |
| Deployment | Render |
| Scheduling | APScheduler (Cron Jobs) |
 
---
 
## Core Features (Technical Deep-Dive)
 
### 1. Resume Context Injection
 
**The Problem:** Generic interviewers ask the same questions regardless of who you are. Real interviewers read your resume and probe your actual experience.
 
**The Solution:** When a user uploads their resume (PDF), the raw PDF binary is sent directly to Google Gemini, which returns a structured JSON summary covering skills, projects, experience, and tech stack. This summary is stored as **JSONB** in a dedicated `UserResume` table (1:1 with `User`) and **automatically injected into the system prompt of every LLM call** across all interview sessions.
 
```
PDF Upload
    │
    ▼
Gemini API ──► Structured JSON Resume Summary
    │
    ▼
Stored in UserResume.resume_data (JSONB, PostgreSQL)
    │           (1:1 linked to User)
    ▼
Fetched and injected into every Interview System Prompt
    │
    ▼
"You mentioned FastAPI on your resume. Walk me through
 how you handled authentication in your last project."
```
 
**Key Design Choices:**
- `UserResume` is a **separate table** from `User` — resume data can be updated independently without touching auth/identity data
- `resume_data` stored as **JSONB** — allows structured field access later (e.g., extract skills list for analytics) without a schema migration
- No embedding/vector storage — the LLM-generated summary fits in every prompt's context window cleanly, keeping the architecture simple without a vector DB dependency
 
---
 
### 2. Multi-Turn AI Interview Engine
 
Each interview is a **stateful, persistent conversation** — not a one-shot Q&A.
 
**How it works:**
 
1. User starts an interview → a new `Interview` record is created with `status = "active"`.
2. Every user message and AI response is stored as an `InterviewTurn` record (with role: `user` or `assistant`).
3. On each new LLM call, the **full conversation history** is reconstructed from the database and sent as context — giving the model complete memory.
4. The system prompt includes: interview type persona + resume summary + conversation history.
 
**This enables:**
- Follow-up questions based on previous answers
- Clarification requests ("Can you explain what you meant by O(n log n) here?")
- Deep dives into specific topics mentioned by the user
- Behavioral consistency across the entire interview session
 
```
System Prompt = [Interviewer Persona] + [Resume Summary] + [Conversation History]
                                                            ▲
                                              Fetched from InterviewTurn table
                                              (all turns for this interview_id)
```
 
---
 
### 3. Coding Round Simulation
 
The coding round replicates what an actual technical screen feels like — an IDE in the browser, real code submission, and an AI that reviews code the way a human interviewer would.
 
**Technical Implementation:**
- **Embedded CodeMirror IDE** with syntax highlighting for: Python, Java, C, C++, JavaScript
- On code submission, the code string is embedded directly into the LLM prompt
- The LLM responds **as an interviewer** — not as a code checker
 
**LLM Behavior Rules (enforced via prompt engineering):**
- Points out bugs, missed edge cases, and logical errors
- Asks the candidate to identify and fix issues themselves
- **Never reveals the correct solution directly**
- If code is correct, pivots to follow-up questions: time complexity, space complexity, alternative approaches, edge cases
- Maintains full conversational context from earlier in the interview
 
> **Example Flow:**  
> Candidate submits a binary search with an off-by-one error →  
> AI: *"Your logic looks close, but consider what happens when the search space reduces to one element. What does `mid` evaluate to in that case?"*
 
---
 
### 4. Structured Evaluation Engine
 
When an interview ends, the **entire conversation** is sent to Gemini with a strict evaluation prompt that enforces a JSON response schema:
 
```json
{
  "score": 72,
  "strengths": ["Good understanding of time complexity", "Clear communication"],
  "weaknesses": ["Missed edge cases in tree traversal", "Shallow on system design trade-offs"],
  "improvements": ["Practice sliding window problems", "Review CAP theorem in depth"],
  "final_verdict": "Above Average — Ready for mid-level interviews with focused prep"
}
```
 
**Anti-inflation Guard:**  
A manual check is applied before the LLM call — if the interview has **zero user turns** (the user never answered anything), the score is hard-set to `0`. This prevents the LLM from hallucinating positive scores for empty sessions.
 
**Storage:** The result is stored in the `InterviewEvaluation` table linked 1:1 to the `Interview` record, making it permanently accessible in the history dashboard.
 
---
 
### 5. Interview History & Dashboard
 
Users can view all their past interviews from a persistent history dashboard:
 
- **List view:** All past interviews with interview type, date, and score (0–100)
- **Detailed view:** Click any interview to expand a full evaluation breakdown — strengths, weaknesses, improvement suggestions, and final verdict
 
This enables candidates to track progress over time, revisit weak areas, and compare performance across interview types.
 
---
 
### 6. Authentication & Security
 
**JWT-based Auth with HttpOnly Cookies**
 
- Tokens stored in **HttpOnly cookies** — not `localStorage` — preventing XSS-based token theft
- All interview routes are protected and validate that the requesting user owns the interview (`interview.user_id == current_user.id`)
- Database-level user isolation: every query is scoped by `user_id`
 
**Forgot Password Flow:**
1. User requests password reset → OTP generated and emailed via **SMTP (Gmail)**
2. OTP verified → user sets new password
3. All auth events are logged (login, logout, password change, failed attempts)
 
> ⚠️ **Known Limitation:** The SMTP Gmail integration breaks on Render's free tier due to port restrictions. A dedicated email service API (SendGrid/Resend) is planned for production.
 
---
 
## Database Design
 
### Entity-Relationship Diagram
 
```
┌──────────────────────────┐          ┌───────────────────────────┐
│           User           │          │        UserResume         │
├──────────────────────────┤          ├───────────────────────────┤
│ user_id (PK)             │ 1──────1 │ id (PK)                   │
│ name                     │          │ user_id (FK, unique)      │
│ email (unique)           │          │ resume_data (JSONB)       │◄── LLM-generated
│ password_hashed          │          │ updated_at                │    structured summary
│ phone_no (unique)        │          └───────────────────────────┘
│ created_at               │
└────────────┬─────────────┘
             │ 1                       ┌───────────────────────────┐
             │                    1───►│   PasswordResetSession    │
             │ N                  N    ├───────────────────────────┤
┌────────────▼─────────────┐          │ session_id (PK, UUID)     │
│        Interview         │          │ user_id (FK)              │
├──────────────────────────┤          │ otp                       │
│ interview_id (PK)        │          │ otp_expiry                │
│ user_id (FK → User)      │          │ reset_attempts            │
│ interview_type           │◄── "dsa",│ verified (Boolean)        │
│ difficulty               │    "hr", │ created_at                │
│ mode                     │    etc.  └───────────────────────────┘
│ language                 │◄── coding lang (nullable)
│ status                   │◄── "scheduled"|"active"|"completed"
│ created_at               │
│ ended_at                 │
└──────┬───────────────────┘
       │                    └──────────────────────────┐
       │ 1                                              │ 1
       │                                               │
       │ N                                              │ 1
┌──────▼──────────────────┐          ┌─────────────────▼──────────┐
│     InterviewTurn       │          │    InterviewEvaluation     │
├─────────────────────────┤          ├────────────────────────────┤
│ turn_id (PK)            │          │ evaluation_id (PK)         │
│ interview_id (FK)       │          │ interview_id (FK)          │
│ role                    │◄─"user"  │ score (Integer, 0–100)     │
│                         │  or      │ strengths (String)         │
│                         │  "asst"  │ weaknesses (String)        │
│ content (String)        │          │ improvements (String)      │
│ created_at              │          │ final_verdict (String)     │
└─────────────────────────┘          │ created_at                 │
                                     └────────────────────────────┘
```
 
### All Tables at a Glance
 
| Table | PK Type | Key Columns | Notes |
|---|---|---|---|
| `users` | Integer | `email` (unique), `phone_no` (unique) | Core identity table |
| `user_resumes` | Integer | `user_id` (unique FK), `resume_data` (JSONB) | 1:1 with User; JSONB for flexible LLM output |
| `password_reset_sessions` | UUID | `otp`, `otp_expiry`, `reset_attempts`, `verified` | UUID PK for unguessable session IDs |
| `interviews` | Integer | `interview_type`, `difficulty`, `mode`, `language`, `status` | `language` nullable (only set for coding rounds) |
| `interview_turns` | Integer | `role`, `content`, `interview_id` (FK) | Full conversation history; cleaned by cron |
| `interview_evaluations` | Integer | `score`, `strengths`, `weaknesses`, `improvements`, `final_verdict` | 1:1 with Interview; kept permanently |
 
### Relationships Summary
 
| Relationship | Cardinality | Details |
|---|---|---|
| User → Interview | One-to-Many | A user can run many interview sessions |
| User → UserResume | One-to-One | One resume summary per user; `unique=True` on FK |
| User → PasswordResetSession | One-to-Many | Multiple reset sessions allowed (e.g., re-requests) |
| Interview → InterviewTurn | One-to-Many | Every message in the conversation is a turn |
| Interview → InterviewEvaluation | One-to-One | `cascade="all, delete"` — evaluation deleted with interview |
 
### Key Design Decisions
 
- **`UserResume` as a separate table** — decouples resume data from the `User` entity; allows independent updates (re-upload without touching auth data) and keeps the `users` table lean
- **`resume_data` as JSONB** — the LLM returns a structured summary; JSONB allows querying individual fields later (e.g., extract skills for analytics) without a schema change
- **`PasswordResetSession.session_id` as UUID** — integer PKs are enumerable and guessable; a UUID primary key makes OTP session IDs unguessable, adding a layer of security to the reset flow
- **`Interview.language` nullable** — only populated for coding-round interviews; NULL signals non-coding sessions cleanly without a separate table
- **`InterviewEvaluation` with `cascade="all, delete"`** — if an interview is deleted, its evaluation is automatically removed, maintaining referential integrity
- **`InterviewTurn` cleaned by cron, `InterviewEvaluation` kept forever** — turns grow unboundedly; evaluations are compact distilled artifacts. Cron targets turns only, keeping the DB lean while preserving all user-visible history
- **PostgreSQL over SQLite** — required for JSONB (`resume_data`), UUID primary keys, `CASCADE` deletes, and production-grade concurrency
 
---
 
## Infrastructure & Reliability
 
### Rate Limiting
 
Rate limiting is applied **per route** based on the computational and cost weight of each operation. Limits are enforced per IP/user to prevent LLM abuse and protect API quota.
 
| Route / Operation | Rate Limit | Reason |
|---|---|---|
| Next interview question (LLM) | 5 req/min | Core LLM call — highest cost |
| Start interview | 2 req/min | Prevents session flooding |
| Code feedback (LLM) | 5 req/min | Heavy Gemini call with code context |
| Final evaluation (LLM) | 2 req/min | Full conversation processing |
| Login | 2 req/min | Brute-force protection |
| Resend OTP | 2 req/min | Abuse prevention on password reset |
 
---
 
### Cron Job — Conversation Cleanup
 
Old raw conversation data (`InterviewTurn` rows) is automatically cleaned up on a scheduled cron job.
 
**Rationale:** Once an interview is evaluated, the raw conversation turns are no longer needed — the evaluation (score, strengths, weaknesses, verdict) is the distilled artifact. Retaining millions of turn rows indefinitely would bloat the database.
 
**Behavior:**
- Runs on a configurable schedule
- Deletes `InterviewTurn` records older than a defined threshold (e.g., 7 days)
- `Interview` and `InterviewEvaluation` records are **never deleted** — history and scores are permanent
- Ensures database stays lean without sacrificing user-visible history
 
```
InterviewTurn (raw turns) ──► Deleted after threshold
Interview                 ──► Kept permanently
InterviewEvaluation       ──► Kept permanently
```
 
---
 
### Logging & Observability
 
Structured logs are emitted to stdout and visible in Render's **Live Tail** dashboard in production. Key events logged across the application lifecycle:
 
**Authentication Events:**
- User registered, logged in, logged out
- Password changed, OTP requested/verified
- Auth failures (invalid token, unauthorized access attempt)
 
**Interview Lifecycle:**
- Interview started (type, user_id)
- Each LLM call initiated and completed (with latency in ms)
- Code submission received
- Evaluation triggered and completed
 
**Performance Metrics:**
- LLM API call latency
- Database query latency (critical queries)
- Evaluation processing time
 
**Error Tracking:**
- LLM API failures / timeouts
- Database exceptions
- Unexpected server errors (500s)
 
> In production on Render, all logs are visible in real-time via the **Live Tail** feature under the service dashboard.
 
---
 
## Project Structure
 
```
app/
│
├── auth/                   # JWT auth, login, register, password reset
│   ├── router.py
│   ├── service.py
│   └── utils.py            # Password hashing, token generation, OTP
│
├── mock_interview/         # Core interview logic
│   ├── router.py           # Interview start, turn, end, history endpoints
│   ├── service.py          # Business logic layer
│   └── cron.py             # APScheduler job for conversation cleanup
│
├── llm/                    # LLM abstraction layer
│   ├── gemini_client.py    # Gemini API wrapper
│   ├── prompt_builder.py   # System prompt construction (resume + persona + history)
│   └── evaluator.py        # Structured evaluation prompt + JSON parsing
│
├── models/                 # SQLAlchemy ORM models
│   └── models.py           # User, Interview, InterviewTurn, InterviewEvaluation
│
├── schemas/                # Pydantic request/response schemas
│
├── database/               # DB session, engine, connection setup
│
├── middleware/             # Rate limiting middleware
│
├── templates/              # Jinja2 HTML templates
│   ├── interview.html      # Live interview page
│   ├── coding.html         # CodeMirror coding round
│   ├── history.html        # Interview history dashboard
│   └── evaluation.html     # Evaluation popup
│
├── static/                 # CSS, JS assets
│
└── main.py                 # FastAPI app init, router registration, scheduler start
```
 
---
 
## Local Setup
 
### Prerequisites
 
- Python 3.10+
- PostgreSQL 14+
- Node.js (optional, for frontend asset builds)
- A Google Gemini API key ([Get one here](https://aistudio.google.com/app/apikey))
 
### Step 1 — Clone the Repository
 
```bash
git clone https://github.com/harshraj0049/nexthire-ai-interview-platform.git
cd nexthire-ai-interview-platform
```
 
### Step 2 — Create a Virtual Environment
 
```bash
python -m venv venv
 
# Activate on Windows
venv\Scripts\activate
 
# Activate on Mac/Linux
source venv/bin/activate
```
 
### Step 3 — Install Dependencies
 
```bash
pip install -r requirements.txt
```
 
### Step 4 — Set Up PostgreSQL
 
Create the database:
 
```sql
CREATE DATABASE NextHire_AI;
```
 
### Step 5 — Configure Environment Variables
 
Create a `.env` file in the project root:
 
```env
DATABASE_URL=postgresql+psycopg2://your_username:your_password@localhost:5432/NextHire_AI
GEMINI_API_KEY=your_gemini_api_key_here
SECRET_KEY=your_jwt_secret_key_here
SMTP_EMAIL=your_gmail@gmail.com
SMTP_PASSWORD=your_gmail_app_password
```
 
### Step 6 — Run Database Migrations
 
```bash
# Tables are created automatically via SQLAlchemy on first run
# Or run explicitly:
python -c "from app.database.db import Base, engine; Base.metadata.create_all(bind=engine)"
```
 
### Step 7 — Start the Server
 
```bash
uvicorn app.main:app --reload
```
 
Visit: [http://localhost:8000](http://localhost:8000)
 
---
 
## Environment Variables
 
| Variable | Description | Required |
|---|---|---|
| `DATABASE_URL` | PostgreSQL connection string | ✅ |
| `GEMINI_API_KEY` | Google Gemini API key | ✅ |
| `SECRET_KEY` | JWT signing secret (use a strong random string) | ✅ |
| `SMTP_EMAIL` | Gmail address for OTP emails | ⚠️ Optional (for password reset) |
| `SMTP_PASSWORD` | Gmail app password | ⚠️ Optional (for password reset) |
 
---
 
## API Reference
 
| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `POST` | `/auth/register` | ❌ | Register new user |
| `POST` | `/auth/login` | ❌ | Login, sets HttpOnly JWT cookie |
| `POST` | `/auth/logout` | ✅ | Clear JWT cookie |
| `POST` | `/auth/forgot-password` | ❌ | Send OTP to email |
| `POST` | `/auth/verify-otp` | ❌ | Verify OTP |
| `POST` | `/auth/reset-password` | ❌ | Set new password after OTP |
| `POST` | `/interview/start` | ✅ | Start new interview session |
| `POST` | `/interview/next-question` | ✅ | Send answer, get next question |
| `POST` | `/interview/submit-code` | ✅ | Submit code, get LLM code review |
| `POST` | `/interview/end` | ✅ | End interview, trigger evaluation |
| `GET` | `/interview/history` | ✅ | List all past interviews with scores |
| `GET` | `/interview/evaluation/{id}` | ✅ | Get detailed evaluation for interview |
| `POST` | `/user/upload-resume` | ✅ | Upload PDF, generate & store summary |
 
---
 
## Design Decisions & Engineering Tradeoffs
 
**Full Conversation Persistence over Summary Storage**  
Storing every turn individually allows the final evaluation to have access to the complete interview — including nuances, hesitations, follow-ups, and corrections. A summary would lose fidelity.
 
**LLM-as-Summarizer for Resume, not Vector Embeddings**  
Vector similarity search would add infrastructure complexity (a vector DB) for marginal gain. A compact Gemini-generated summary fits in every prompt's context window cleanly, keeps the system simple, and works reliably at this scale.
 
**Strict JSON Schema for Evaluation**  
Open-ended LLM evaluation responses are unparseable and inconsistent. Enforcing a strict JSON output schema makes scores comparable, storable, and display-ready without post-processing ambiguity.
 
**Per-Route Rate Limiting (not global)**  
A global rate limit would penalize normal browsing while letting a user spam LLM routes. Per-route limits target the expensive operations specifically — protecting Gemini API quota while keeping the UX smooth.
 
**Cron-based Conversation Cleanup**  
Keeping evaluation results forever (they're tiny) while purging raw turn data (can grow large) balances storage cost against user value. Users never lose their score history.
 
**HttpOnly Cookie over localStorage for JWT**  
`localStorage` is accessible by JavaScript and vulnerable to XSS attacks. HttpOnly cookies are invisible to JS and sent automatically with every request — a more secure default for session management.
 
---
 
## Roadmap
 
- [ ] Async SQLAlchemy for non-blocking DB calls
- [ ] Replace SMTP Gmail with a production email API (SendGrid / Resend)
- [ ] Performance analytics dashboard (score trends over time, per-domain breakdown)
- [ ] PDF export of evaluation report
- [ ] Docker + Docker Compose for one-command local setup
- [ ] Interview replay (step through conversation history turn by turn)
- [ ] Admin dashboard for platform analytics
 
---
 
## Author
 
**Harsh Raj**  
B.Tech CSE — KIIT University  
AI/ML Enthusiast | Backend Developer
 
📧 [harshraj.hr08@gmail.com](mailto:harshraj.hr08@gmail.com)  
💼 [linkedin.com/in/harsh-raj-6760b7354](https://linkedin.com/in/harsh-raj-6760b7354)  
🐙 [github.com/harshraj0049](https://github.com/harshraj0049)
 
---
 
<div align="center">
  <sub>Built with FastAPI, PostgreSQL, Google Gemini, and a lot of interview prep anxiety.</sub>
</div>

## License

MIT License

Copyright (c) 2026 Harsh Raj

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.