# Local setup (Windows PowerShell)

Prerequisites: Python 3.12, Node 20+, Git, Docker Desktop (for Redis), a Supabase project (or the local-db profile).

## 1. Accounts and keys (see DEPLOYMENT.md for click-by-click)
Telegram bot token, your numeric Telegram ID, Supabase connection string, Anthropic API key, Voyage AI key
(or OpenAI key for embeddings). Claude has no embeddings API, so RAG needs one of those two.

## 2. Backend
```powershell
cd trading-assistant\backend
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env        # then edit .env
python -c "import secrets;print(secrets.token_urlsafe(32))"   # use for TELEGRAM_WEBHOOK_SECRET, and again for JWT_SECRET
cd ..; docker compose up -d redis; cd backend
alembic upgrade head               # creates the pgvector extension, all tables, RLS
python -m scripts.create_admin you@example.com --role owner --telegram-id 123456789
python -m scripts.seed_knowledge   # loads the 16-topic starter curriculum + embeddings (needs embedding key)
uvicorn app.main:app --reload --port 8000
```
Telegram only delivers webhooks to public HTTPS. For local testing run a tunnel (e.g. `ngrok http 8000`) and set
`PUBLIC_BASE_URL` to the tunnel URL before starting uvicorn; the app registers the webhook on startup.
Check it: `python -m scripts.set_webhook --info`.

## 3. Dashboard
```powershell
cd ..\admin-dashboard
Copy-Item .env.example .env.local   # BACKEND_URL=http://localhost:8000
npm install
npm run dev                          # http://localhost:3000, sign in with the admin you created
```
Set `DASHBOARD_ORIGIN=http://localhost:3000` in the backend `.env`.

## 4. Tests
```powershell
cd ..\backend
pytest -q
```
Tests use fakes and never call paid APIs.

## Environment variable checklist
| Variable | Required | Notes |
|---|---|---|
| TELEGRAM_BOT_TOKEN | yes | BotFather |
| TELEGRAM_WEBHOOK_SECRET | yes | 16+ chars, `A-Za-z0-9_-` only (Telegram rule) |
| ADMIN_TELEGRAM_IDS | yes | comma-separated; receive alerts, may use admin commands |
| DATABASE_URL | yes | `postgresql+asyncpg://...:6543/postgres` (Supabase pooler) |
| REDIS_URL | yes | |
| ANTHROPIC_API_KEY, CLAUDE_MODEL | yes | confirm model id in the Anthropic console |
| EMBEDDING_PROVIDER, VOYAGE_API_KEY / OPENAI_API_KEY | yes for RAG | |
| JWT_SECRET | yes | 32+ chars |
| PUBLIC_BASE_URL | production | backend's public https URL |
| DASHBOARD_ORIGIN | yes | dashboard URL (CORS) |
