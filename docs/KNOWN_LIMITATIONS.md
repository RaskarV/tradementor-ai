# Known limitations

1. **Unexecuted code:** see TESTING_REPORT.md. Treat the framework-dependent code as a careful first draft.
2. **Heuristic compliance:** regex + context rules are strong against the listed patterns but can be evaded by novel
   phrasing and can over-block unusual educational wording. No rule set is complete. An LLM-based second classifier
   hook exists (`ExternalClassifier`) but **no adapter is implemented**; add one if you want semantic checks.
   Negation/warning dismissals are sentence-level, so a deliberately misleading sentence that contains a scam word can slip through.
3. **Model id:** `CLAUDE_MODEL` default must be confirmed against your Anthropic console.
4. **Embeddings need a second vendor** (Voyage or OpenAI). Changing dimension requires a migration and rebuild.
5. **Starter curriculum is general, unsourced prose.** Review it and add authoritative sources; the bot only cites URLs you store.
6. **No market data by design:** the bot cannot answer live-price questions and will say so.
7. **Baseline migration** creates the schema from current models; later changes must use normal migrations.
8. **Single-region, single-process** design; background processing uses FastAPI tasks (no durable queue). A crash mid-update loses that update (it is deduped, not retried).
9. **Conversation history in Redis** is a cache of the last 12 turns; very long-term memory/summaries are not implemented (`conversations.summary` is unused).
10. **Languages:** the LLM replies in the stated language, but static bot texts and compliance rules are English-only; non-English drafts get weaker rule coverage.
11. **Admin Telegram commands** need your Telegram ID linked to a dashboard account to assign tickets.
12. **Not legal or regulatory advice.** Indian rules on investment advice and research (SEBI) are your responsibility; get qualified counsel before public launch.
13. **Repository layer:** `database/repositories/` is an empty package; data access lives in `services/` and the route modules. Fine at this size, refactor if it grows.
