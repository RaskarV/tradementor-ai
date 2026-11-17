# Testing report

## What was actually executed (in the build sandbox, no network)
Python 3.12; the 6 suites below were run with a small local runner because `pytest` could not be installed offline.
They use only the standard library plus PyJWT, so they exercise the modules that have no framework dependency.

| Suite | Tests | Covers |
|---|---|---|
| test_compliance | 17 | every rule fires (27 violation phrasings) and 20 legitimate texts stay clear; both spec examples; policy config; custom-regex validation; fail-closed paths; add-only external classifier; normalisation evasions; audit sink failure |
| test_risk_calculator | 11 | spec example, short side, rounding, zero quantity, leverage warning, 11 invalid inputs, limits, number parsing, explanation, output passes the gate |
| test_sender_and_e2e | 10 | user text -> fake LLM -> gate -> fake Telegram: cleared and blocked flows, admin alert format, fail-closed, admin-alert failure, LLM outage and alert, memory, grounding and citations, injection text stays in the user turn, message splitting, **no-bypass source scan** |
| test_misc | 4 | onboarding parsing, ticket state machine/codes, password hashing + JWT + roles, document sanitising/chunking |
| test_texts | 2 | every static bot string passes the gate; list-negation does not hide claims |
| test_seed | 1 | starter curriculum is clean and complete |

**Result: 45 passed, 0 failed.** `compileall` succeeds for all Python.
Bugs found by these tests during the build and fixed: sentence splitting at "e.g.", negation scope across commas
(two directions: too wide and too narrow), a vacuous no-bypass assertion, and a method name that collided with Telegram's `reply`.

## Written but NOT executed (need `pip install -r requirements.txt`, Postgres, Redis, Telegram)
- `tests/test_webhook.py` (3 tests: secret, dedupe, size/format) needs fastapi + aiogram.
- All database code (models, repositories, migrations), aiogram handlers/middlewares/FSM, the admin REST API, and the
  Claude/OpenAI/Voyage/OpenAI-embeddings clients have only been syntax-checked.
- The Next.js dashboard has not been installed, type-checked, built or opened in a browser.
- No test yet for: DB operations, onboarding through real aiogram, API authorisation per route, handoff against a database.
  Spec items 1, 2, 11, 12, 13 (partly), 14 and the live Telegram path therefore still need testing in your environment.

Expect small fixes on first run (imports, typing, aiogram/SQLAlchemy API details). Run `pytest -q`, then the live checklist in DEPLOYMENT.md.
