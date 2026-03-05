# Job Scrappy 🤖

A personal job application pipeline that scrapes multiple job boards, detects job language, collects recruiter emails, and sends personalized applications via Gmail — all automated on a daily cron.

[![License: MIT](https://img.shields.io/badge/License-MIT-violet.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](https://python.org)
[![Next.js](https://img.shields.io/badge/Next.js-14-black.svg)](https://nextjs.org)

---

## What it does

1. **Scrapes** job boards every day at 08:00 BRT for frontend/fullstack roles in Brazil
2. **Detects language** (PT/EN) from title + description using `langdetect`
3. **Collects emails** from job descriptions via regex
4. **Filters** blocked seniority levels (e.g. senior, pleno) via `BLOCKED_KEYWORDS`
5. **Sends** personalized PT or EN email templates via Gmail API (max 30/day)
6. **Portal** — local Next.js dashboard to review jobs, apply, or dismiss

## Sources

| Scraper | Type | Notes |
|---|---|---|
| [Gupy](https://gupy.io) | JSON API | Primary BR source, `isActive=true` filter |
| [Adzuna](https://developer.adzuna.com) | JSON API | Requires `ADZUNA_APP_ID` + `ADZUNA_APP_KEY` |
| [Jooble](https://jooble.org) | JSON API | Requires `JOOBLE_API_KEY`, scoped to `country=br` |
| [Google Custom Search](https://developers.google.com/custom-search) | JSON API | Requires `GOOGLE_API_KEY` + `GOOGLE_CSE_ID` |
| [RemoteOK](https://remoteok.com) | JSON API | No auth, filters by frontend/JS tags |
| [Arbeitnow](https://arbeitnow.com) | JSON API | No auth, filters remote or Brazil location |
| [Programathor](https://programathor.com.br) | HTML scrape | No auth, BS4 parser |

All sources run **in parallel** via `asyncio.gather` and are merged + deduped by URL before processing.

## Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.11 + FastAPI + SQLite |
| Frontend | Next.js 14 + TypeScript + Tailwind + shadcn/ui |
| Scraping | httpx + BeautifulSoup4 |
| Email | Gmail API (OAuth2) |
| Deploy | Railway (backend) + Vercel (frontend) |
| Cron | GitHub Actions (daily 08:00 BRT) |

## Getting started

### 1. Clone & install

```bash
git clone https://github.com/your-username/job-scrappy.git
cd job-scrappy

# Backend
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Frontend
cd ../frontend
npm install
```

### 2. Configure environment

```bash
cp .env.example .env
# Fill in the values (see .env.example for all variables)
```

**Required:**
- `GMAIL_CLIENT_ID`, `GMAIL_CLIENT_SECRET`, `GMAIL_REFRESH_TOKEN` — Gmail OAuth2
- `SENDER_NAME`, `SENDER_EMAIL` — used in email templates

**Optional (scrapers disabled if missing):**
- `ADZUNA_APP_ID` + `ADZUNA_APP_KEY`
- `JOOBLE_API_KEY`
- `GOOGLE_API_KEY` + `GOOGLE_CSE_ID`

### 3. Run locally

```bash
# Backend (http://localhost:8000)
cd backend && uvicorn app.main:app --reload

# Frontend (http://localhost:3000)
cd frontend && npm run dev

# Trigger the pipeline manually
curl -X POST http://localhost:8000/api/pipeline/scrape
```

### 4. SQLite migration (first run after update)

If upgrading from an older version, run once:
```sql
ALTER TABLE job ADD COLUMN dismissed BOOLEAN NOT NULL DEFAULT 0;
```

## Environment variables

See [`.env.example`](.env.example) for the full list.

## Key limits

- **Max 30 emails/day** — hard-coded, never overrides
- **No duplicate sends** — jobs with `status=sent` are skipped
- **LinkedIn is post-MVP** — risk of ban, not implemented

## Portal

The dashboard at `localhost:3000` lets you:
- View all scraped jobs with status, language badge, and email
- Filter by **status** (new / sent / skipped) and **language** (Português / English)
- **Aplicar** — opens job URL in new tab and marks as dismissed
- **Ignorar** — dismisses without opening

## License

[MIT](LICENSE) © 2026 Kai Alvarenga
