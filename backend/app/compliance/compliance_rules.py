"""Deterministic rule set. Standard library only.

Each Rule has regex patterns plus `dismiss_on`: the context types in which a regex hit is
NOT a violation (e.g. "no one can guarantee returns" is a negated mention, not a claim).
Context decisions are made by compliance_classifier.ContextClassifier.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from app.compliance.compliance_models import CompliancePolicy, CustomRule, Severity

_I = re.IGNORECASE | re.UNICODE

# A number that looks like a price/level (not "50 companies"): currency-prefixed, comma-grouped,
# 3+ digits, or decimal.
NUMP = (r"(?:(?:rs\.?|₹|inr|\$)\s?\d[\d,]*(?:\.\d+)?|\d{1,3}(?:,\d{2,3})+(?:\.\d+)?"
        r"|\d{3,}(?:\.\d+)?|\d+\.\d+)")
INDEX = (r"(?:nifty\s?(?:50|bank|next\s?50|it|fin(?:ancial)?\s?services)?|bank\s?nifty|fin\s?nifty|"
         r"sensex|midcap\s?\d*|smallcap\s?\d*|dow(?:\s+jones)?|nasdaq|s&p\s?500|gold|silver|"
         r"crude(?:\s+oil)?|bitcoin|btc|usd[/-]?inr)")
SPECIFIC_SUBJ = (r"(?:nifty(?:\s?50)?|bank\s?nifty|sensex|this\s+(?:stock|share|index|market|counter)|"
                 r"(?-i:[A-Z]{4,}))")
GENERIC_SUBJ = r"(?:the\s+(?:market|markets|index|stock|share|price)|stocks?|prices?|shares?)"
DIRECTION = (r"(?:rise|go\s+up|fall|go\s+down|crash|drop|rally|surge|moon|double|triple|hit|reach|"
             r"touch|break\s+out|skyrocket|soar|tank)")


@dataclass(frozen=True)
class Rule:
    rule_id: str
    category: str
    severity: Severity
    patterns: tuple
    description: str
    dismiss_on: frozenset = frozenset()


def _r(rule_id, category, severity, pats, desc, dismiss=()):
    return Rule(rule_id, category, severity, tuple(re.compile(p, _I) for p in pats), desc,
                frozenset(dismiss))


BUILTIN_RULES: tuple = (
    _r("GUARANTEED_PROFIT", "guaranteed_profit", Severity.CRITICAL, [
        r"\bguarantee(?:s|d|ing)?\s+(?:\w+\s+){0,3}?(?:profits?|gains?|wins?|winnings)\b",
        r"\b(?:profits?|gains?)\s+(?:is|are|will\s+be)\s+(?:100\s*%\s+)?(?:guaranteed|assured)\b",
        r"\b(?:sure[- ]?shot|sure[- ]?fire|assured)\s+(?:profits?|gains?|wins?)\b",
        r"\b100\s*%\s*(?:profit|win(?:ning)?|success|accura(?:te|cy)|sure)\b",
        r"\byou\s+(?:will|are\s+going\s+to|'ll)\s+(?:definitely\s+|surely\s+|certainly\s+|always\s+)?"
        r"(?:make|earn|get|gain)\s+(?:a\s+)?(?:money|profits?)\b",
    ], "Claims or implies guaranteed profit", ("negation", "warning")),
    _r("GUARANTEED_RETURNS", "guaranteed_return", Severity.CRITICAL, [
        r"\bguarantee(?:s|d|ing)?\s+(?:\w+\s+){0,3}?(?:returns?|yields?|income|outcomes?|results?|payouts?)\b",
        r"\b(?:returns?|yields?|income)\s+(?:is|are|will\s+be)\s+(?:100\s*%\s+)?(?:guaranteed|assured)\b",
        r"\b(?:assured|fixed|guaranteed|sure)\s+(?:monthly\s+|daily\s+|weekly\s+)?(?:returns?|income|payouts?)\b",
        r"\bguarantee(?:s|d)?\s+(?:of\s+)?\d+(?:\.\d+)?\s*%",
    ], "Claims or implies guaranteed returns", ("negation", "warning")),
    _r("NO_LOSS_CLAIM", "risk_free", Severity.CRITICAL, [
        r"\bcan(?:'t|not|\s+not)\s+(?:possibly\s+)?lose\b",
        r"\bnever\s+lose\b(?!\s+(?:discipline|sight|track|focus|patience|your\s+(?:cool|focus|discipline)))",
        r"\bimpossible\s+to\s+lose\b",
        r"\bno\s+chance\s+of\s+(?:loss|losing)\b",
        r"\bloss[- ]proof\b",
    ], "Claims a trader cannot lose", ("warning",)),
    _r("RISK_FREE", "risk_free", Severity.HIGH, [
        r"\brisk[- ]?free\b(?!\s+(?:rate|asset|assets|interest|benchmark))",
        r"\bzero[- ]risk\b", r"\bno[- ]risk\b",
        r"\b(?:100\s*%|completely|totally|absolutely|entirely)\s+safe\b",
        r"\bsafe\s+(?:bet|investment|trade|stock|option)\b",
        r"\bcan(?:'t|not)\s+go\s+wrong\b",
        r"\bwithout\s+(?:any\s+)?risk\b",
    ], "Calls an investment or trade risk-free or safe", ("negation", "warning")),
    _r("LIVE_QUOTE", "live_quote", Severity.HIGH, [
        rf"\b{INDEX}\b[^.\n]{{0,40}}?\b(?:is|are|at|stands?|trading|trades|traded|closed|closes|opened|"
        rf"opens|hit|touched|currently|quoted|near|around)\b[^.\n]{{0,25}}?{NUMP}",
        rf"\b(?:current(?:ly)?|live|right\s+now|as\s+of\s+now|at\s+the\s+moment|today(?:'s)?|latest)\b"
        rf"[^.\n]{{0,40}}?\b(?:price|quote|level|value|trading|trades|closing|close)\b[^.\n]{{0,30}}?{NUMP}",
        rf"\b(?:trading|trades|traded|quoted|priced)\s+at\s+{NUMP}",
        rf"\b(?:market\s+price|share\s+price|stock\s+price|current\s+price|ltp|cmp)\b[^.\n]{{0,20}}?"
        rf"(?:\bis\b|\bof\b|\bat\b|:)\s*{NUMP}",
    ], "States a live or current market price the bot cannot verify", ("hypothetical",)),
    _r("PERSONAL_RECOMMENDATION", "personal_recommendation", Severity.HIGH, [
        r"\bi\s+(?:strongly\s+|would\s+)?(?:recommend|suggest|advise)\s+(?:that\s+)?(?:you\s+)?(?:to\s+)?"
        r"(?:buy|sell|short|invest\s+in|enter|go\s+long|go\s+short)\b",
        r"\byou\s+(?:should|must|need\s+to|ought\s+to|have\s+to)\s+(?:definitely\s+|now\s+|immediately\s+|also\s+)?"
        r"(?:buy|sell|short)(?!\s+(?:only|after|when|if|low|high|based))\b",
        r"\byou\s+(?:should|must|need\s+to|ought\s+to|have\s+to)\s+(?:definitely\s+|now\s+)?"
        r"(?:invest\s+in|go\s+long|go\s+short|book\s+profits?)\b",
        r"\b(?:go|going)\s+(?:long|short)\s+(?:on|in)\b",
        r"\b(?:buy|sell|short)\s+(?:it\s+|this\s+|that\s+|them\s+)?(?:now|today|immediately|asap|right\s+away)\b",
        rf"\b(?:buy|sell)\s+(?:at|above|below|near)\s+{NUMP}",
        r"\b(?:good|great|perfect|ideal|best|right)\s+(?:level|price|time|entry|point|zone)\s+to\s+"
        r"(?:buy|sell|enter|short|go\s+long)\b",
        r"\b(?:buy|sell)\s+\d{4,6}\s*(?:ce|pe|call|put)\b",
    ], "Tells the user to buy or sell", ("warning",)),
    _r("STOCK_PREDICTION", "stock_prediction", Severity.HIGH, [
        rf"\b{SPECIFIC_SUBJ}\s+(?:will|is\s+going\s+to|is\s+sure\s+to|is\s+bound\s+to|is\s+set\s+to)\s+"
        rf"(?:definitely\s+|surely\s+|certainly\s+|soon\s+)?{DIRECTION}\b",
        rf"\b{GENERIC_SUBJ}\s+(?:will|is\s+going\s+to)\s+(?:definitely|surely|certainly|undoubtedly|for\s+sure)"
        rf"\s+{DIRECTION}\b",
        rf"\b{GENERIC_SUBJ}\s+is\s+(?:sure|bound|certain|guaranteed)\s+to\s+{DIRECTION}\b",
        rf"\b(?:price\s+target|target\s+price)\s+(?:for\s+\S+\s+)?(?:of|is|:)\s*{NUMP}",
    ], "Predicts a price move as fact", ("negation", "warning", "hypothetical")),
    _r("MISLEADING_PROMISE", "misleading_promise", Severity.HIGH, [
        r"\b(?:double|triple|10x|100x)\s+your\s+(?:money|capital|investment|account|savings)\b",
        r"\bget[- ]rich[- ]quick\b",
        r"\bovernight\s+(?:riches|wealth|millionaire|success)\b",
        r"\b(?:easy|effortless|passive)\s+(?:money|income)\s+(?:from|with|by)\s+trading\b",
        r"\b(?:quit|leave)\s+your\s+(?:job|9[- ]to[- ]5)\b[^.\n]{0,30}\btrad",
        r"\b(?:earn|make)\s+(?:rs\.?|₹|inr)?\s?\d[\d,]*\s*(?:per|a|every|each)\s+(?:day|week|month)\b",
        r"\b(?:deposit|invest|trade)\s+(?:now|today|immediately|right\s+away)\b",
        r"\b(?:limited[- ]time|last\s+chance|act\s+now|don't\s+miss\s+out|hurry\s+up)\b",
        r"\bonly\s+\d+\s+(?:spots|seats)\s+left\b",
    ], "Misleading promise or pressure to deposit/trade", ("negation", "warning", "hypothetical")),
    _r("UNVERIFIED_STATISTIC", "unverified_statistic", Severity.MEDIUM, [
        r"\b\d{1,3}(?:\.\d+)?\s*%\s+of\s+(?:all\s+)?(?:retail\s+|new\s+|day\s+|f&o\s+|individual\s+)?"
        r"(?:traders|investors|beginners|people|trades|stocks|day\s+traders)\b",
        r"\b(?:historically|on\s+average|averag(?:e|ed|es))\b[^.\n]{0,50}\b\d+(?:\.\d+)?\s*%",
    ], "Statistic without a named source or grounding in the knowledge base",
       ("attribution", "grounded")),
    _r("UNSOURCED_RESEARCH_CLAIM", "unverified_statistic", Severity.LOW, [
        r"\b(?:studies|research|surveys?|statistics)\s+(?:show|shows|prove|proves|confirm|confirms|found|"
        r"indicate|indicates|suggest|suggests)\b",
    ], "Research claim without a named source (logged, not blocked)", ("attribution",)),
    _r("REGULATORY_CLAIM", "regulatory", Severity.HIGH, [
        r"\b(?:i\s+am|we\s+are|i'm)\s+(?:a\s+)?(?:sebi[- ]registered|registered\s+(?:investment\s+)?advis[eo]r|"
        r"certified\s+financial\s+planner)",
        r"\bsebi[- ](?:approved|certified|endorsed)\b",
        r"\b(?:rbi|sebi|nse|bse)\s+(?:guarantees?|insures?)\b",
        r"\b(?:guaranteed|assured|insured)\s+by\s+(?:sebi|nse|bse|rbi)\b",
    ], "Implies regulatory registration or backing", ("negation", "warning")),
)

_NESTED_QUANT = re.compile(r"\([^)]*[+*][^)]*\)\s*[+*{]")


def validate_pattern(pattern: str) -> re.Pattern:
    """Compile an admin-supplied regex, rejecting oversized or obviously backtracking-prone ones."""
    if not pattern or len(pattern) > 300:
        raise ValueError("pattern must be 1-300 characters")
    if _NESTED_QUANT.search(pattern):
        raise ValueError("nested quantifiers are not allowed (regex DoS risk)")
    try:
        return re.compile(pattern, _I)
    except re.error as e:
        raise ValueError(f"invalid regex: {e}") from e


def build_rules(policy: CompliancePolicy) -> list:
    rules = []
    for r in BUILTIN_RULES:
        if r.rule_id in policy.disabled_rules:
            continue
        sev = policy.severity_overrides.get(r.rule_id)
        if sev is not None:
            r = Rule(r.rule_id, r.category, Severity.parse(sev), r.patterns, r.description, r.dismiss_on)
        rules.append(r)
    for c in policy.custom_rules:
        if c.rule_id in policy.disabled_rules:
            continue
        rules.append(Rule(c.rule_id, c.category, Severity.parse(c.severity), (validate_pattern(c.pattern),),
                          "Administrator-configured rule", frozenset()))
    phrases = [p.strip() for p in policy.regulatory_phrases if p and p.strip()]
    if phrases and "REGULATORY_CONFIG" not in policy.disabled_rules:
        pat = re.compile("|".join(re.escape(p) for p in phrases), _I)
        rules.append(Rule("REGULATORY_CONFIG", "regulatory", Severity.HIGH, (pat,),
                          "Configured regulatory restriction", frozenset()))
    return rules
