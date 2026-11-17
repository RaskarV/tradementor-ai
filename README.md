# TradeMentor AI

An AI trading **education** and risk-management assistant that runs on Telegram, with an independent
fail-closed compliance gate, RAG over curated educational material, a position-size calculator, human
educator handoff, and an admin dashboard.

It does **not** trade, connect to brokers, give buy/sell recommendations, or quote live prices.

```
trading-assistant/
  backend/            FastAPI + aiogram 3 + SQLAlchemy + Alembic (Python 3.12)
  admin-dashboard/    Next.js 14 + TypeScript + Tailwind + Recharts
  docs/               SETUP, DEPLOYMENT, ARCHITECTURE, COMPLIANCE, API, DATABASE, TESTING, LIMITATIONS, CHECKLIST
  docker-compose.yml  Redis (+ optional local Postgres/pgvector and backend)
  render.yaml         Render blueprint (backend)
```

Start with **docs/SETUP.md** (local) then **docs/DEPLOYMENT.md** (live). Read **docs/TESTING_REPORT.md** and
**docs/KNOWN_LIMITATIONS.md** before trusting anything: some parts were verified by running tests, others could
only be written and syntax-checked.

Key guarantees (enforced by code and tests):
- Handlers never hold the Telegram `Bot`; only `SafeSender` sends, and it calls the compliance engine first.
- If the engine errors, users get a static message and an admin alert; the draft is never sent.
- The compliance package imports nothing from the AI, bot or database layers.
