---
name: job-scraper
description: Use when implementing, modifying or debugging job board scraping logic, including Gupy API integration, deduplication, email extraction from job descriptions, and error handling in scrapers.
---

## Overview
Scrapes Gupy public JSON API by keyword + city. Normalizes into Job model. Extracts recruiter email from description via regex.

## Gupy endpoint
GET https://portal.api.gupy.io/api/v1/jobs?jobName={keyword}&city={city}&limit=20
Returns `data[]` with: name, company.name, jobUrl, description.

## Pattern
```python
async with httpx.AsyncClient(headers={"User-Agent": "Mozilla/5.0"}) as client:
    await asyncio.sleep(1.5)
    r = await client.get(URL, params=params)
    r.raise_for_status()

Catch all exceptions per request — log warning and continue.
Email regex

python
re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")

Apply to description. Take first match only.
Common errors

    429: increase sleep to 3s, skip

    Empty data[]: city not found, skip silently

    Missing jobUrl: skip entry

text

***

**`.agent/skills/email-sender/SKILL.md`**
```markdown
---
name: email-sender
description: Use when implementing or debugging Gmail API OAuth2 authentication, email sending, rate limit enforcement, or PT/EN template rendering.
---

## Overview
Sends emails via Gmail API OAuth2. Hard limit: 30/day. Renders PT or EN template by job language.

## OAuth2
```python
creds = Credentials(
    token=None,
    refresh_token=os.getenv("GMAIL_REFRESH_TOKEN"),
    client_id=os.getenv("GMAIL_CLIENT_ID"),
    client_secret=os.getenv("GMAIL_CLIENT_SECRET"),
    token_uri="https://oauth2.googleapis.com/token"
)
service = build("gmail", "v1", credentials=creds)

Never use SMTP. Never log token values.
Rate limit (always before sending)

python
today = session.query(EmailLog).filter(func.date(EmailLog.sent_at) == date.today()).count()
if today >= 30:
    raise RateLimitExceeded()

Common errors

    invalid_grant: refresh token expired, user must re-auth

    dailyLimitExceeded: reduce limit to 20/day

text

***

**`.agent/skills/pipeline/SKILL.md`**
```markdown
---
name: pipeline
description: Use when implementing or debugging the daily orchestration pipeline that coordinates scraping, language detection, email collection, and email sending into a single automated flow.
---

## Flow
1. Load config (keywords, cities, daily limit)
2. fetch_gupy_jobs(keywords, cities)
3. Per job: skip if URL in DB → detect_language → extract email → save with status
4. Per job with email (respecting limit): render_template → send_email → update status → insert EmailLog
5. Return {scraped, emails_found, sent, errors}

## Critical rules
- Never exceed daily limit — check before each send
- Never reprocess status "sent"
- Catch errors per job — never stop the full pipeline
- Always return summary even if all jobs fail