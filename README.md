# Job Scrappy 🤖

Automated job application pipeline. Scrapes multiple Brazilian job boards daily, detects job language (PT/EN), collects recruiter emails, and sends personalized applications via Gmail — all from a local Next.js dashboard.

[![License: MIT](https://img.shields.io/badge/License-MIT-violet.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](https://python.org)
[![Next.js](https://img.shields.io/badge/Next.js-14-black.svg)](https://nextjs.org)

---

## Stack

| Layer | Technology |
|---|---|
| API | FastAPI + slowapi (rate limiting) |
| ORM | SQLModel + SQLite |
| Scraping | httpx + BeautifulSoup4 |
| Email | Gmail API (OAuth2) |
| Frontend | Next.js 14 + TypeScript + Tailwind + shadcn/ui |
| Deploy | Railway (backend) · Vercel (frontend) |
| CI | GitHub Actions |

---

## Scrapers

| Source | Auth | Notes |
|---|---|---|
| **Gupy** | None | Primary BR source, `isActive=true` filter |
| **Google Custom Search** | `GOOGLE_API_KEY` + `GOOGLE_CSE_ID` | Optional |
| **Jooble** | `JOOBLE_API_KEY` | Optional, scoped to `country=br` |
| **RemoteOK** | None | Filters by frontend/JS tags |
| **Adzuna** | `ADZUNA_APP_ID` + `ADZUNA_APP_KEY` | Optional, pages 1–3 per keyword |
| **Arbeitnow** | None | Filters `remote=true` or Brazil location |
| **Programathor** | None | HTML scrape, 4 category pages × 3 pages |

All sources run in parallel via `asyncio.gather` and are deduplicated by URL before processing.

---

## Running locally

### Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

cp ../.env.example ../.env
# Fill in values (see Environment variables below)

uvicorn app.main:app --reload
# → http://localhost:8000
```

### Frontend

```bash
cd frontend
npm install

# create frontend/.env.local
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local

npm run dev
# → http://localhost:3000
```

### Docker (full stack)

```bash
cp .env.example .env   # fill in values
docker compose up --build
```

---

## Environment variables

See [`.env.example`](.env.example) for the full list. Summary:

### Required

| Variable | Description |
|---|---|
| `GMAIL_CLIENT_ID` | Gmail OAuth2 client ID |
| `GMAIL_CLIENT_SECRET` | Gmail OAuth2 client secret |
| `GMAIL_REFRESH_TOKEN` | Gmail OAuth2 refresh token |
| `API_KEY` | Secret key for protected endpoints (see Authentication) |
| `SENDER_NAME` | Your name — used in email templates |
| `SENDER_EMAIL` | Your email address |

### Optional scrapers (disabled if not set)

| Variable | Scraper |
|---|---|
| `GOOGLE_API_KEY` + `GOOGLE_CSE_ID` | Google Custom Search |
| `JOOBLE_API_KEY` | Jooble |
| `ADZUNA_APP_ID` + `ADZUNA_APP_KEY` | Adzuna |

### Pipeline config

| Variable | Default | Description |
|---|---|---|
| `SEARCH_KEYWORDS` | `developer` | Comma-separated keywords for Gupy/Jooble |
| `SEARCH_CITIES` | `São Paulo` | Comma-separated cities for Gupy |
| `BLOCKED_KEYWORDS` | _(empty)_ | Titles containing these keywords are skipped |
| `DATABASE_URL` | `sqlite:///./jobscout.db` | SQLite path |
| `FRONTEND_URL` | `http://localhost:3000` | Allowed CORS origin |

---

## Authentication

The `POST /api/pipeline/*` and `GET /api/emails/*` endpoints require the `X-API-Key` header matching the `API_KEY` environment variable.

```bash
curl -X POST http://localhost:8000/api/pipeline/scrape \
  -H "X-API-Key: your_secret_key"
```

Rate limit: **5 requests / minute / IP**. Exceeding returns `429 Too Many Requests`.

Unauthenticated requests return `403 Forbidden`.

---

## Key limits

- **Max 30 emails/day** — hard-coded, never overrides
- **No duplicate sends** — jobs with `status=sent` are skipped
- **LinkedIn is post-MVP** — risk of ban

---

## License

[MIT](LICENSE) © 2026 Kai Alvarenga
