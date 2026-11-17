# Compliance gate

Pipeline: `AI draft -> normalize -> rule scan (regex) -> context classifier -> [optional external classifier, add-only]
-> decision -> (blocked) safe alternative -> re-validation -> audit log -> delivery`.

## Rules (compliance_rules.py)
| Rule | Category | Severity | Dismissed in context |
|---|---|---|---|
| GUARANTEED_PROFIT | guaranteed_profit | CRITICAL | negation, scam warning |
| GUARANTEED_RETURNS | guaranteed_return | CRITICAL | negation, scam warning |
| NO_LOSS_CLAIM | risk_free | CRITICAL | scam warning |
| RISK_FREE | risk_free | HIGH | negation, scam warning |
| LIVE_QUOTE | live_quote | HIGH | hypothetical example |
| PERSONAL_RECOMMENDATION | personal_recommendation | HIGH | scam warning |
| STOCK_PREDICTION | stock_prediction | HIGH | negation, warning, hypothetical |
| MISLEADING_PROMISE | misleading_promise | HIGH | negation, warning, hypothetical |
| UNVERIFIED_STATISTIC | unverified_statistic | MEDIUM | named source, or numbers present in retrieved KB text |
| UNSOURCED_RESEARCH_CLAIM | unverified_statistic | LOW | named source (logged only) |
| REGULATORY_CLAIM | regulatory | HIGH | negation, warning |
| REGULATORY_CONFIG / custom | regulatory / custom | configurable | never |

Messages block when any confirmed match has severity >= `block_threshold` (default MEDIUM).

## Context classification
A regex hit is a candidate. The classifier looks at the sentence: negation within the clause ("no one can guarantee
returns"; scope carries across short list items but not across a new clause with its own subject), scam/warning words,
hypothetical markers ("suppose", "for example"), attribution (SEBI, NSE, "according to") and grounding in retrieved text.
Text is normalised first (NFKC, zero-width and bidi characters removed, curly quotes, common Cyrillic look-alikes).

## Safety properties
- Fail closed: any exception becomes `ComplianceUnavailable`; the sender then sends a static message only.
- Safe alternatives are re-validated; if one fails, a static fallback (also validated) is used; if that fails, the engine refuses.
- Independent of the model: no AI imports; text in a draft cannot change policy. The optional external (LLM) classifier
  can only add matches, never clear one, and can be made mandatory with `external_required`.
- Admin-supplied regexes are validated (length cap, nested-quantifier rejection). Weakening a built-in rule needs an owner.
- Human-written educator replies pass the same gate and are withheld (not rewritten) when blocked.
- Every static bot string is checked by a test to pass the gate.

## Extending
Add a `Rule` to `BUILTIN_RULES` with a positive case in `tests/test_compliance.py::MUST_FIRE` and any legitimate
phrasing it might wrongly catch in `MUST_CLEAR`; the test `test_every_builtin_rule_has_a_positive_case` enforces coverage.
Custom rules and regulatory phrases can also be added live from the dashboard.
