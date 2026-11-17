# Architecture

```
Telegram -> POST /webhook/telegram (secret header, size limit, update_id dedupe in Redis)
  -> aiogram Dispatcher: outer middlewares [rate limit -> DB session -> user context]
  -> handler (start/onboarding FSM, risk FSM, learn, human, reset, delete, admin cmds, free chat)
  -> ConversationManager: memory(Redis) + RAG(pgvector) + LLMProvider(Claude|OpenAI)   [draft = untrusted]
  -> SafeSender -> ComplianceEngine (normalize -> rules -> context classifier -> decision -> safe alternative
                                     -> re-validate -> audit log) -> Telegram
FastAPI admin API (/api/*, JWT + RBAC) <- Next.js dashboard (httpOnly-cookie proxy)
```

## Modules
- `compliance/` standard-library only; no imports from ai, bot or database. Receives text, returns a decision.
- `bot/sender.py` the only code path that delivers user-facing text. `notifications/telegram_alerts.py` is the only
  other sender and writes only to configured administrator IDs. A test (`test_no_bypass...`) parses the source and
  fails if any other module calls Telegram send methods.
- `ai/` provider interface (`llm_provider.py`), Claude/OpenAI implementations, prompt templates, Redis memory,
  conversation manager. The base system prompt lives in code; administrators can only append guidance.
- `knowledge/` sanitising, chunking, embeddings (Voyage/OpenAI), pgvector retrieval, starter curriculum.
- `trading/` Decimal-based calculator and validators (standard library only, never executes trades).
- `support/` ticket state machine and manager (pending -> assigned -> answered -> closed).
- `services/` users, conversations, compliance persistence, runtime settings (cached, refreshed every 30 s).

## Message flow details
1. Webhook verifies `X-Telegram-Bot-Api-Secret-Token` (constant-time), rejects bodies over `MAX_REQUEST_BYTES`,
   validates the Update, dedupes with `SET NX EX 86400`, then processes in a background task (fast 200 to Telegram).
2. Middlewares: per-user rate limit (Redis), one DB transaction per update (commit/rollback), user upsert + profile.
3. Free text: persist the user message (unique `telegram_update_id` blocks duplicates), retrieve knowledge,
   call the LLM, send through SafeSender with the retrieved text as grounding context for statistic checks.
4. Persist what was actually delivered; a blocked draft is stored in `original_draft` only for audit and is never put back into model context.
5. Citations are generated from stored document titles/URLs, never from model output.

## Failure behaviour
| Failure | Behaviour |
|---|---|
| Compliance engine raises | static error message to user, nothing unchecked sent, admin alert |
| LLM error | static unavailable message (also gate-checked); admin alert after 3 consecutive failures |
| Retrieval/embedding error | answer without reference material |
| Admin alert delivery fails | logged; user flow continues |
| Audit-log DB write fails | logged; the decision still stands (a block is still a block) |
| Telegram 429 | one retry after `retry_after`; user blocked bot is swallowed |
