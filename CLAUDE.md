# JobScript — Contexto para Claude

## O que o projeto faz
Automação de candidaturas a vagas: scraping de portais de vagas por palavra-chave + cidade, coleta de emails de recrutadores, detecção de idioma (PT/EN), envio de emails personalizados via Gmail API.

## Stack
- Backend: Python 3.14 + FastAPI + PostgreSQL (Railway)
- Frontend: Next.js 14 + TypeScript + Tailwind + shadcn/ui
- Scraping: httpx + asyncio
- Email: Gmail API (OAuth2) + Hunter.io (opcional) + Snov.io (opcional)
- Deploy: Railway (backend) + Vercel (frontend)
- Cron: GitHub Actions (diário 08:00 BRT)

## Regras críticas

### 1. NUNCA criar arquivos com comentários
- Sem comentários explicativos de código
- Sem docstrings em funções novas
- Sem comentários de bloco
- Código deve ser auto-explanatório

### 2. Arquitetura de scrapers
- Um scraper por empresa em `backend/app/scrapers/`
- Assinatura: `async def fetch_<empresa>_jobs(keywords: list[str], cities: list[str]) -> list[dict]`
- Retorno: lista com `{title, company, url, description, email}`
- Registrar no `asyncio.gather()` em `orchestrator.py`

### 3. Rate limits e proteção
- Google CSE: máx 80 req/dia (padrão 80 de 100 free)
- Indeed BR: via ScraperAPI proxy (1000 req/mês free)
- Gmail: máx 30 emails/dia (hard limit)
- Delays entre requests: 1.5-2.0s

## Comandos principais
```bash
cd backend && uvicorn app.main:app --reload
cd frontend && npm run dev
curl -X POST http://localhost:8000/api/pipeline/run
cd backend && pytest
```

## Variáveis de ambiente principais
- `GMAIL_CLIENT_ID`, `GMAIL_CLIENT_SECRET`, `GMAIL_REFRESH_TOKEN` (Gmail OAuth)
- `SCRAPER_API_KEY` (Indeed BR via ScraperAPI)
- `HUNTER_API_KEY` (enriquecimento de emails, 25 req/mês free)
- `GOOGLE_API_KEY`, `GOOGLE_CSE_ID` (Google Custom Search, 100 req/dia free)
- `SEARCH_KEYWORDS`, `SEARCH_CITIES` (configuração de busca)

## Estrutura do projeto
```
backend/app/
├── scrapers/          (um arquivo por empresa)
├── services/
│   ├── orchestrator.py
│   ├── email_enricher.py
│   ├── email_sender.py
│   └── lang_detector.py
├── api/
│   ├── pipeline.py
│   ├── jobs.py
│   └── config.py
└── models.py
```

## Testes
- Usar pytest para testes de scrapers
- Rodar `pytest` antes de commit
- Coverage mínima: 70%

## Commits
- Formato: `feat:`, `fix:`, `refactor:` seguindo convenção
- Descrever o "por quê", não o "o quê"
