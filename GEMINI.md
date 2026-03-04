# JobScout — Project Context

## What this project does
Automates job applications: scrapes job boards by keyword + city, collects recruiter emails, detects job language (PT/EN), and sends personalized emails via Gmail API.

## Owner
Kai Alvarenga — Full-Stack Developer (React/Next.js/TypeScript/Python). Fluent in PT and EN.

## Stack
- Backend: Python 3.11 + FastAPI + SQLite (MVP)
- Frontend: Next.js 14 + TypeScript + Tailwind + shadcn/ui
- Scraping: httpx + BeautifulSoup4
- Email: Gmail API (OAuth2, scope: gmail.send)
- Deploy: Railway (backend) + Vercel (frontend)
- Cron: GitHub Actions (daily 08:00 BRT)

## Key commands
```bash
cd backend && uvicorn app.main:app --reload
cd frontend && npm run dev
curl -X POST http://localhost:8000/api/pipeline/run
cd backend && pytest

Architecture decisions

    SQLite no MVP, sem auth no dashboard (local only)

    Máximo 30 emails/dia (hard limit — nunca ultrapassar)

    Gupy como scraper principal (API JSON pública)

    LinkedIn pós-MVP (risco de ban)

    langdetect para detecção de idioma, heurística por keywords como fallback

    Hunter.io opcional (free tier: 25/mês)

Environment variables

text
GMAIL_CLIENT_ID=
GMAIL_CLIENT_SECRET=
GMAIL_REFRESH_TOKEN=
HUNTER_API_KEY=
DATABASE_URL=sqlite:///./jobscout.db
FRONTEND_URL=http://localhost:3000

Email templates

Subject PT: Candidatura para {job_title} na {company}
Subject EN: Application for {job_title} at {company}
Variables: {job_title} {company} {sender_name} {contact_info} {whatsapp_link} {linkedin_link} {github_link} {portfolio}
Project structure

text
jobscout/
├── backend/app/
│   ├── main.py
│   ├── models.py
│   ├── database.py
│   ├── scrapers/gupy.py
│   ├── services/email_sender.py
│   ├── services/lang_detector.py
│   ├── services/template_engine.py
│   ├── services/orchestrator.py
│   └── api/jobs.py, emails.py, config.py
├── frontend/src/app/
├── .agent/
├── GEMINI.md
└── .antigravity

text

***

**`.antigravity`**
```yaml
project: jobscout
description: Personal job application automation tool

agent:
  confirm_before_destructive: true
  create_plan_before_implement: true
  max_files_per_change: 10

stack:
  backend: python
  frontend: nextjs
  database: sqlite
  testing: pytest

conventions:
  python:
    type_hints: required
    max_function_lines: 40
  typescript:
    strict: true
    no_any: true
    components: functional_only

testing:
  backend: pytest
  run_before_commit: true
  coverage_minimum: 70
