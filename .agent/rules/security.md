---
trigger: always_on
---

- Never hardcode credentials, tokens, or API keys — always read from environment variables
- Never log GMAIL_REFRESH_TOKEN or any OAuth token value
- Add realistic User-Agent header on all scraping requests
- 1-2 second delay between scraping requests
- Sanitize all user inputs (keywords, cities) before using in URLs
- CORS restricted to FRONTEND_URL env var only
- .env and OAuth token files always in .gitignore
