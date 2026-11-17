"""Independent, fail-closed compliance gate. Standard library only.

This module imports nothing from the AI, bot, or database packages, so the model cannot
influence it. Pipeline: normalize -> regex rules -> context classifier -> (optional external
classifier, add-only) -> decision -> safe alternative -> re-validation -> audit log.
"""
from __future__ import annotations

import logging
import re
import unicodedata
from typing import Optional

from app.compliance.compliance_classifier import ContextClassifier, ExternalClassifier
from app.compliance.compliance_logger import ComplianceLogger
from app.compliance.compliance_models import (CompliancePolicy, ComplianceResult, ReviewContext,
                                              RuleMatch, Verdict)
from app.compliance.compliance_rules import build_rules

log = logging.getLogger("compliance")
MAX_REVIEW_CHARS = 20_000
MAX_HITS_PER_RULE = 25


class ComplianceUnavailable(Exception):
    """Raised when a decision cannot be made. Callers must NOT send the draft."""


STATIC_FALLBACK = ("I'm not able to share that response. I can help with trading concepts, risk "
                   "management and the position size calculator. What would you like to explore?")

SAFE_ALTERNATIVES = {
    "live_quote": ("Let me help you understand the factors traders generally consider when evaluating "
                   "market levels. I cannot verify live market prices or guarantee investment outcomes."),
    "personal_recommendation": ("I can't tell you what to buy or sell. I can explain how to evaluate a "
                                "trade yourself, including risk, position size and stop-loss placement."),
    "guaranteed_profit": ("No trading approach can promise profits, and every trade carries a risk of "
                          "loss. I can explain how traders measure and limit risk if that would help."),
    "guaranteed_return": ("No one can promise returns in the market, and losses are always possible. I can "
                          "explain how traders think about risk and position sizing."),
    "risk_free": ("Every trade and investment carries risk, and some can lose most of their value. I can "
                  "walk you through how risk is measured and managed."),
    "stock_prediction": ("I can't predict where prices will go. I can explain how traders analyse charts "
                         "and how they plan for being wrong."),
    "misleading_promise": ("I can't make promises about trading results, and there is no rush to "
                           "act. I can help you learn the basics at your own pace."),
    "unverified_statistic": ("I don't have a verified source for that figure, so I won't state it. I can "
                             "explain the concept or point you to topics in the knowledge base."),
    "regulatory": ("I'm an educational assistant and not a registered advisor, and I can't make claims "
                   "about regulatory approval. I can help you learn trading concepts."),
    "custom": STATIC_FALLBACK,
}
PRIORITY = ["live_quote", "personal_recommendation", "guaranteed_profit", "guaranteed_return",
            "risk_free", "stock_prediction", "misleading_promise", "unverified_statistic",
            "regulatory", "custom"]

_ZW = re.compile("[\u200b-\u200f\u202a-\u202e\u2060-\u2064\ufeff\u00ad]")
_QUOTES = re.compile("[\u2018\u2019\u02bc`\u00b4]")
_DASHES = re.compile("[\u2010-\u2015\u2212]")
_HOMOGLYPHS = str.maketrans("аеорсхуіјАЕОРСХ", "aeopcxyijAEOPCX")


def normalize(text: str) -> str:
    t = unicodedata.normalize("NFKC", text)
    t = _ZW.sub("", t)
    t = _QUOTES.sub("'", t)
    t = _DASHES.sub("-", t)
    t = t.translate(_HOMOGLYPHS)
    return re.sub(r"[ \t]+", " ", t)


class ComplianceEngine:
    def __init__(self, policy: Optional[CompliancePolicy] = None,
                 classifier: Optional[ContextClassifier] = None,
                 external: Optional[ExternalClassifier] = None,
                 logger: Optional[ComplianceLogger] = None):
        self._classifier = classifier or ContextClassifier()
        self._external = external
        self._logger = logger or ComplianceLogger()
        self.update_policy(policy or CompliancePolicy())

    def update_policy(self, policy: CompliancePolicy) -> None:
        rules = build_rules(policy)  # raises on a bad custom pattern; the old policy stays active
        self._policy, self._rules = policy, rules

    @property
    def policy(self) -> CompliancePolicy:
        return self._policy

    def scan(self, text: str, ctx: Optional[ReviewContext] = None) -> list:
        """Deterministic synchronous scan. Returns confirmed matches of every severity."""
        ctx = ctx or ReviewContext()
        norm = normalize(text)
        if len(norm) > MAX_REVIEW_CHARS:
            raise ComplianceUnavailable("message too long to review")
        found: list = []
        for rule in self._rules:
            hits = 0
            for pat in rule.patterns:
                for m in pat.finditer(norm):
                    hits += 1
                    if hits > MAX_HITS_PER_RULE:
                        break
                    if self._classifier.assess(rule, norm, m.start(), m.end(), ctx).dismissed:
                        continue
                    found.append(RuleMatch(rule.rule_id, rule.category, rule.severity,
                                           m.group(0).strip()[:200]))
        return found

    def _alternative(self, matches: list) -> str:
        cats = {m.category for m in matches}
        for c in PRIORITY:
            if c in cats:
                return SAFE_ALTERNATIVES[c]
        return STATIC_FALLBACK

    async def review(self, text: str, *, message_type: str = "reply",
                     context: Optional[ReviewContext] = None, user_id: Optional[int] = None,
                     conversation_id: Optional[int] = None) -> ComplianceResult:
        if not isinstance(text, str):
            raise ComplianceUnavailable("draft is not text")
        ctx = context or ReviewContext()
        try:
            matches = self.scan(text, ctx)
            if self._external is not None:
                try:
                    for m in await self._external.classify(normalize(text), ctx):
                        matches.append(RuleMatch(m.rule_id, m.category, m.severity, m.excerpt, "external"))
                except Exception as e:
                    if self._policy.external_required:
                        raise ComplianceUnavailable("external classifier failed") from e
                    log.warning("external classifier failed; continuing with deterministic rules")
            threshold = self._policy.block_threshold
            if not any(m.severity >= threshold for m in matches):
                result = ComplianceResult(Verdict.CLEARED, text, text, tuple(matches), message_type)
            else:
                alt = self._alternative(matches)
                if any(m.severity >= threshold for m in self.scan(alt, ctx)):  # re-validate
                    alt = STATIC_FALLBACK
                    if any(m.severity >= threshold for m in self.scan(alt, ctx)):
                        raise ComplianceUnavailable("static fallback violates policy")
                result = ComplianceResult(Verdict.BLOCKED, alt, text, tuple(matches), message_type, True)
        except ComplianceUnavailable:
            raise
        except Exception as e:
            raise ComplianceUnavailable(f"compliance error: {type(e).__name__}") from e
        await self._logger.record(result, user_id, conversation_id)
        return result
