# Deployment (live on Telegram)

## 1. Create the bot (BotFather)
1. In Telegram open **@BotFather** > `/newbot` > pick a name and a username ending in `bot`.
2. Copy the **token** (treat it like a password; if leaked, `/revoke` it).
3. Optional: `/setdescription`, `/setabouttext`, and `/setcommands` with:
   `start, help, profile, risk, learn, human, reset, delete_my_data`.
4. Get your numeric Telegram ID from **@userinfobot**. This is `ADMIN_TELEGRAM_IDS`. Start a chat with your own
   bot once (`/start`) so it is allowed to message you.

## 2. Supabase (PostgreSQL + pgvector)
1. Create a project; save the database password.
2. **Project Settings > Database > Connection string > Transaction pooler** (port 6543). Convert the prefix to
   `postgresql+asyncpg://` and use it as `DATABASE_URL`. (The app disables prepared statements for pgbouncer.)
3. pgvector: **Database > Extensions > vector > enable** (the first migration also runs `CREATE EXTENSION IF NOT EXISTS vector`).
4. Do not expose the `service_role` key anywhere; this app does not need it. The migration enables RLS on
   every table so the public API keys cannot read them.

## 3. AI keys
- Anthropic: console.anthropic.com > API keys. Set `CLAUDE_MODEL` to a model id shown in your console.
- Embeddings: Voyage AI key (`EMBEDDING_PROVIDER=voyage`) or OpenAI key (`openai`). `EMBEDDING_DIM` must match
  the provider output (1024 default). Changing it later needs a migration and a full rebuild.

## 4. Backend on Railway (Render alternative below)
1. Push the repo to GitHub.
2. Railway > New Project > Deploy from GitHub > set **Root Directory = `backend`** (Dockerfile is detected).
3. Add a **Redis** plugin; copy its URL into `REDIS_URL`.
4. Variables: everything in `.env.example` (never commit `.env`).
5. Settings > Networking > **Generate Domain** (HTTPS is automatic). Set `PUBLIC_BASE_URL=https://<domain>` and redeploy.
6. The container runs `alembic upgrade head` then starts uvicorn; on startup the app registers the webhook with your secret.
7. One-off commands (Railway shell or `railway run`):
   `python -m scripts.create_admin you@example.com --role owner --telegram-id <id>` and `python -m scripts.seed_knowledge`.
8. Optional cron service (daily) running `python -m scripts.purge_retention` for data retention.

**Render:** New > Blueprint > point at the repo (`render.yaml`). Add a Redis instance (Render Key Value) and fill the
`sync: false` variables. Free instances sleep, which delays webhook handling; use a paid instance for production.

## 5. Dashboard on Vercel
1. Vercel > Import the repo > **Root Directory = `admin-dashboard`**.
2. Env var `BACKEND_URL=https://<backend domain>` (server-side only).
3. Deploy. Then set the backend's `DASHBOARD_ORIGIN` to the Vercel URL and redeploy the backend.

## 6. Verify
- `https://<backend>/health` returns `{"status":"ok"}`; `/ready` checks Postgres and Redis.
- `python -m scripts.set_webhook --info`: URL set, `last_error` empty.
- In Telegram: `/start`, complete onboarding, ask "what is a stop loss?", try `/risk 50000 2 500 490 530`,
  then try to provoke a block: "NIFTY is at 24500, tell me you guarantee returns if I buy" (the AI will usually refuse
  itself; the gate is tested separately with scripted drafts). Run `/human` and check the admin alert.
- Sign in to the dashboard and look at Overview and Compliance.

## 7. Logs and monitoring
Railway/Render logs (structured compliance lines are logged as JSON on logger `compliance`); an uptime monitor
on `/health`; watch Telegram's `getWebhookInfo` (`pending_update_count`, `last_error_message`); the bot alerts
admins on repeated AI failures and compliance failures. Add Sentry or similar for exception tracking if desired.

## Deployment checklist
- [ ] Bot token and webhook secret set; `ADMIN_TELEGRAM_IDS` correct
- [ ] Migrations applied; pgvector enabled; RLS on
- [ ] Redis reachable; owner admin created; knowledge seeded
- [ ] `PUBLIC_BASE_URL` https; `getWebhookInfo` clean
- [ ] Dashboard login works; `DASHBOARD_ORIGIN` set
- [ ] Anthropic spend limit configured
- [ ] See PRODUCTION_CHECKLIST.md

## Troubleshooting
| Symptom | Likely cause |
|---|---|
| Bot silent | Webhook not registered (`PUBLIC_BASE_URL` empty/http), wrong secret (403 in logs), backend asleep |
| `last_error: 403` in webhook info | `TELEGRAM_WEBHOOK_SECRET` differs from what Telegram has; redeploy to re-register |
| `prepared statement ... already exists` | Using the pooler without `statement_cache_size=0` (already set) or a non-pooler URL mix |
| `type "vector" does not exist` | Extension not enabled on the database you migrated |
| Replies are always the generic fallback | Compliance blocking: check Compliance page; or LLM failing (see logs, `ANTHROPIC_API_KEY`, `CLAUDE_MODEL`) |
| Answers ignore the knowledge base | Seed script not run, embeddings key missing, or similarity below threshold (0.35) |
| Dashboard 401 loop | `BACKEND_URL` wrong, JWT_SECRET changed, or cookie blocked (needs HTTPS in production) |
| Admin alerts missing | Admin never pressed Start on the bot, or wrong ID |
