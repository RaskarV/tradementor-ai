# Production-readiness checklist

Security
- [ ] Secrets only in platform env vars; rotate anything that ever touched git or chat
- [ ] Webhook secret set and verified (`getWebhookInfo` clean); HTTPS only
- [ ] Strong owner password; consider adding 2FA/SSO in front of the dashboard
- [ ] Anthropic/Voyage spend limits and alerts configured
- [ ] RLS enabled (migration) and Supabase service-role key not used anywhere

Compliance and legal
- [ ] Counsel reviewed disclaimers, onboarding text, data handling and SEBI implications
- [ ] Privacy notice linked from the bot description; deletion flow tested end-to-end
- [ ] Red-team the gate with your own phrasings; add cases to `MUST_FIRE` / `MUST_CLEAR`
- [ ] Knowledge base reviewed and sourced; admins briefed on what they may upload

Reliability
- [ ] All tests green in CI (add GitHub Actions: `pip install -r requirements.txt && pytest -q`, `npm run typecheck && npm run build`)
- [ ] Add DB-backed and aiogram flow tests (see TESTING_REPORT)
- [ ] Paid, always-on backend instance; Redis persistence/backups understood
- [ ] Supabase backups/PITR enabled; migration rollback plan
- [ ] Uptime monitor on `/health`; error tracking (Sentry); log retention
- [ ] Retention cron scheduled; load-tested at expected concurrency (LLM latency dominates)

Product
- [ ] Human-support staffing and response-time expectations decided (the bot promises none)
- [ ] Review blocked-message dashboard daily for the first weeks and tune rules
