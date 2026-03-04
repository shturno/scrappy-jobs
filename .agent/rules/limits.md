---
trigger: always_on
---

- Maximum 30 emails/day — check EmailLog before every send, raise RateLimitExceeded if reached
- Never send duplicate emails — check Job.status before sending
- Gupy only in MVP — LinkedIn is post-MVP
- Hunter.io is optional — pipeline works without it
- SQLite only in MVP — no PostgreSQL until explicitly requested
- No dashboard authentication in MVP
