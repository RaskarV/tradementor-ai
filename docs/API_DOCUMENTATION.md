# API

All `/api/*` routes except login require `Authorization: Bearer <JWT>`. Roles: `educator` < `admin` < `owner`
(role is read from the database on every request). OpenAPI docs are disabled in production by design.

| Method | Path | Role | Purpose |
|---|---|---|---|
| POST | /webhook/telegram | secret header | Telegram updates |
| GET | /health, /ready | none | liveness; Postgres+Redis readiness |
| POST | /api/auth/login | none (5 tries/15 min per IP+email) | returns JWT |
| GET | /api/auth/me | any | current admin |
| GET | /api/overview | educator | counters + 14-day series |
| GET | /api/users?q&limit&offset | educator | users (no message content) |
| GET | /api/users/{id} | educator | profile; history ids only if permitted |
| GET | /api/conversations?q | admin | search conversations |
| GET | /api/conversations/{id} | educator* | messages + compliance decisions (*educators only for users with a ticket assigned to them) |
| GET | /api/compliance/logs?decision&rule | admin | audit log |
| GET/PUT | /api/compliance/rules[/{code}] | admin | list; enable/severity (weakening built-ins: owner) |
| POST/DELETE | /api/compliance/rules[/{code}] | admin | custom regex rules |
| GET | /api/support?status | educator (scoped) | tickets |
| GET | /api/support/{id} | educator (scoped) | ticket + context |
| POST | /api/support/{id}/assign | educator (self) / admin (others) | assign |
| POST | /api/support/{id}/reply | educator (scoped) | deliver via Telegram through the gate (422 if blocked) |
| PATCH | /api/support/{id}/status | educator (scoped) | transition (validated) |
| GET/POST/PUT/DELETE | /api/knowledge[/{id}] | admin | documents (re-embeds on change) |
| POST | /api/knowledge/upload, /rebuild | admin | .txt/.md upload; rebuild embeddings |
| GET | /api/settings | admin | runtime settings |
| PUT | /api/settings/{key} | admin | keys: system_prompt_extra, llm, notifications, risk_limits, compliance |
| GET/POST/PATCH | /api/admins | owner | manage administrator access |

Telegram admin commands (IDs in `ADMIN_TELEGRAM_IDS`): `/tickets`, `/assign TM-XXXXXX`, `/reply TM-XXXXXX text`, `/close TM-XXXXXX`.
