# Database schema (PostgreSQL / Supabase, pgvector)

```
users 1-1 user_profiles                      users 1-* conversations 1-* messages
users 1-* support_requests *-0..1 admin_users (assigned_to)    support_requests *-0..1 conversations
users 0..1-* compliance_logs (SET NULL)      knowledge_documents 1-* knowledge_chunks (vector)
compliance_rules, bot_settings, audit_logs *-0..1 admin_users
```
| Table | Notes |
|---|---|
| users | telegram_id unique; last_active_at indexed |
| user_profiles | experience enum, optional learning_capital (CHECK >= 0), language, onboarding_complete |
| conversations | is_active; /reset closes the old one and opens a new one |
| messages | role CHECK; unique telegram_update_id (duplicate protection); original_draft only for blocked drafts; compliance_decision/rules |
| compliance_logs | decision, matched_rules JSON, severity, excerpt, message_type; indexed by time/decision/severity |
| compliance_rules | built-in rows (overrides) and custom regex rules; severity CHECK |
| support_requests | ticket_code unique (TM-XXXXXX); status enum; context_snapshot (last 10 turns) |
| admin_users | scrypt password hash, role enum, optional telegram_id |
| knowledge_documents / knowledge_chunks | HNSW cosine index on `embedding vector(EMBEDDING_DIM)` |
| bot_settings | key/value JSON; no secrets |
| audit_logs | admin actions; user-deletion entries store only a truncated hash of the Telegram ID |

Every table has RLS enabled with no policies (the backend's owner-role connection bypasses it; Supabase public API keys get nothing).
Foreign keys cascade from users, so `/delete_my_data` removes profile, conversations, messages and tickets in one statement.

**Retention:** `python -m scripts.purge_retention` deletes messages, closed tickets and compliance logs older than `RETENTION_DAYS`.
**Migrations:** `0001_initial` builds the schema from the models; make every later change with `alembic revision --autogenerate`.
