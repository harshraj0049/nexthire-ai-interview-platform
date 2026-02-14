🚀 NextHire.AI
AI-Powered Resume-Aware Mock Interview Platform

NextHire.AI is a full-stack AI-driven mock interview system designed to simulate real-world technical interviews with contextual awareness, persistent conversation memory, structured evaluation, and resume-based personalization.

Built with FastAPI, PostgreSQL, SQLAlchemy, and Google Gemini API, the platform replicates real interview pressure and flow while maintaining production-grade backend architecture.

🎯 Why This Project Matters

This is not a chatbot.

It is:

A multi-turn AI interview engine

A resume-aware dynamic questioning system

A persistent conversational evaluation framework

A production-style backend architecture

A real interview simulation tool used for daily preparation

It combines:

Backend engineering

LLM integration

Database modeling

Prompt engineering

Real-time conversational systems

Structured AI evaluation

🧠 Core Features
1️⃣ Resume-Aware Interviewing (Contextual Intelligence)

Users upload resume once

Resume is parsed and summarized

Summary is stored in database

Every interview automatically includes resume context in prompt

The interviewer adapts questions based on:

Claimed skills

Projects

Experience

Technical stack

This replicates how real interviewers question candidates.

2️⃣ Multi-Turn AI Interview Loop

Full conversation stored in database (InterviewTurn table)

Each new LLM call includes full context

Supports:

Clarifications

Follow-ups

Code discussions

Concept deep dives

No artificial “Submit Answer” buttons.
Realistic interview flow.

3️⃣ Coding Round Simulation

Embedded CodeMirror IDE

Multiple language support

Code submission endpoint

LLM responds as interviewer (not evaluator)

Discussion-based technical flow

4️⃣ Structured Final Evaluation Engine

When interview ends:

Entire conversation is evaluated

LLM returns structured JSON:

Score (0–100)

Strengths

Weaknesses

Improvements

Final Verdict

Stored in InterviewEvaluation table

Displayed in evaluation popup UI

Manual guard:
If zero answers → zero score

Prevents inflated AI scoring.

5️⃣ Authentication & Security

JWT-based authentication

HttpOnly cookies

Protected interview routes

Interview ownership validation

Database-level user isolation

6️⃣ PostgreSQL Production Database

Fully migrated from SQLite to PostgreSQL.

Database Entities

User

Interview

InterviewTurn

InterviewEvaluation

Relational Design
User (1) —— (N) Interview  
Interview (1) —— (N) InterviewTurn  
Interview (1) —— (1) InterviewEvaluation


Designed for:

Scalability

Data integrity

Historical tracking

Analytics expansion

🏗 System Architecture
Backend

FastAPI (RESTful API design)

SQLAlchemy ORM

PostgreSQL

Modular service layer

Prompt-building abstraction

LLM integration layer

LLM Integration

Google Gemini API

Structured JSON responses for evaluation

Resume-aware prompt injection

Context-aware conversation memory

Frontend

Jinja2 templates

CodeMirror editor

Speech-to-text

AI voice output

Real-time UI interaction

🧩 Project Structure
app/
│
├── auth/                  
├── mock_interview/        
├── llm/                   
├── models/                
├── schemas/               
├── database/              
├── templates/             
├── static/                
└── main.py


Clear separation of:

Routing

Business logic

Prompt engineering

Database models

Schemas

Authentication

⚙️ How to Run Locally
1️⃣ Clone Repository
git clone https://github.com/harshraj0049/nexthire-ai-interview-platform.git
cd nexthire-ai-interview-platform

2️⃣ Create Virtual Environment
python -m venv venv
venv\Scripts\activate   # Windows
# source venv/bin/activate  # Mac/Linux

3️⃣ Install Dependencies
pip install -r requirements.txt

4️⃣ Setup PostgreSQL

Create database:

CREATE DATABASE NextHire_AI;


Set environment variables:

DATABASE_URL=postgresql+psycopg2://username:password@localhost:5432/NextHire_AI
GEMINI_API_KEY=your_key_here

5️⃣ Run Server
uvicorn app.main:app --reload

📊 Design Decisions & Engineering Tradeoffs
✔ Stored Full Conversation

Instead of only storing Q&A pairs, entire conversation is persisted for:

Realism

Accurate evaluation

Context retention

✔ Structured LLM Output

Used strict JSON schema to:

Prevent vague evaluation

Enforce marking rubric

Avoid hallucinated scoring

✔ Resume Context Injection

Improves:

Question relevance

Technical depth

Behavioral authenticity

✔ PostgreSQL Migration

Ensures:

Production readiness

JSONB support

Relational integrity

Scalability

🚀 Future Roadmap

Async DB migration

Performance analytics dashboard

Interview history tracking UI

PDF export of evaluation

Docker containerization

Admin analytics

Model abstraction layer

👨‍💻 Author

Harsh Raj
B.Tech CSE — KIIT University
AI/ML Enthusiast | Backend Developer

📧 harshraj.hr08@gmail.com

🔗 LinkedIn: https://linkedin.com/in/harsh-raj-6760b7354

🐙 GitHub: https://github.com/harshraj0049
