---
trigger: always_on
---

## Python
- Type hints required on all functions
- Use httpx (async) — not requests library
- Handle scraping errors silently: log and continue, never crash pipeline
- Max 40 lines per function

## TypeScript
- Strict mode, no `any`
- All API calls through lib/api.ts
- shadcn/ui components only — no custom primitives
- Server components by default

## General
- Commits in English, imperative mood
- No commented-out code in commits
- One responsibility per file
