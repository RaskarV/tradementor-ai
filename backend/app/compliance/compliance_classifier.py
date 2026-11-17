"""Context-aware classification for regex hits. Standard library only.

A regex hit is only a *candidate*. The classifier decides whether the surrounding sentence
makes it a real violation (an assertion) or a harmless mention (negation, scam warning,
hypothetical example, attributed statistic, grounded statistic).
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Protocol

from app.compliance.compliance_models import ReviewContext

_I = re.IGNORECASE
NEGATION = re.compile(
    r"\b(?:no|not|never|cannot|can't|cant|won't|wont|nobody|no\s+one|none|neither|nor|isn't|aren't|"
    r"doesn't|don't|didn't|shouldn't|wouldn't|couldn't|without|unable|impossible|myth|unrealistic)\b", _I)
WARNING = re.compile(
    r"\b(?:scams?|scammers?|fraud(?:ulent)?|misleading|red\s+flags?|warning\s+signs?|beware|"
    r"be\s+(?:wary|careful|cautious)|too\s+good\s+to\s+be\s+true|fake|ponzi|illegal)\b", _I)
HYPOTHETICAL = re.compile(
    r"\b(?:suppose|assume|assuming|imagine|hypothetical(?:ly)?|for\s+example|for\s+instance|e\.g\.?|"
    r"let's\s+say|lets\s+say|say\s+(?:a|the|you)|what\s+if|if|scenario|illustrat(?:e|es|ion|ive)|"
    r"sample|example)\b", _I)
ATTRIBUTION = re.compile(
    r"\b(?:according\s+to|as\s+per|per\s+(?:a|the)|source:|study\s+by|report\s+by|published\s+by|"
    r"sebi|nse|bse|rbi|amfi)\b", _I)
_HARD_SPLIT = re.compile(r"[;:()\u2014\u2013]|\b(?:but|however|although|though|yet)\b", _I)
_SUBJECTISH = re.compile(r"\b(?:you|we|i|it|this|they|will|would|shall|can|should|could|must)\b", _I)


_IMPERATIVE_NEG = re.compile(r"\b(?:don't|do\s+not)\s+(?:you\s+)?(?:worry|panic|fret)\b|\bno\s+worries\b", _I)


def _list_like(seg: str) -> bool:
    return len(seg.split()) <= 6 and not _SUBJECTISH.search(seg)
_SENT_BREAK = re.compile(r"(?<!e\.g\.)(?<!i\.e\.)(?<!vs\.)(?<!rs\.)(?<!approx\.)(?<=[.!?])\s+|\n+", re.I)


@dataclass(frozen=True)
class Assessment:
    dismissed: bool
    reason: str = ""


def sentence_bounds(text: str, start: int, end: int) -> tuple:
    s, e = 0, len(text)
    for m in _SENT_BREAK.finditer(text):
        if m.end() <= start:
            s = m.end()
        elif m.start() >= end:
            e = m.start()
            break
    return s, e


class ContextClassifier:
    def assess(self, rule, text: str, start: int, end: int, ctx: ReviewContext) -> Assessment:
        s, e = sentence_bounds(text, start, end)
        sentence = text[s:e]
        if "negation" in rule.dismiss_on and self._negated(text[s:start], text[start:end]):
            return Assessment(True, "negated")
        if "warning" in rule.dismiss_on and WARNING.search(sentence):
            return Assessment(True, "scam/warning context")
        if "hypothetical" in rule.dismiss_on and HYPOTHETICAL.search(sentence):
            return Assessment(True, "hypothetical example")
        if "attribution" in rule.dismiss_on and ATTRIBUTION.search(sentence):
            return Assessment(True, "named source")
        if "grounded" in rule.dismiss_on and ctx.retrieved_text:
            nums = re.findall(r"\d+(?:\.\d+)?", text[start:end])
            if nums and all(n in ctx.retrieved_text for n in nums):
                return Assessment(True, "grounded in retrieved knowledge")
        return Assessment(False)

    @staticmethod
    def _negated(prefix: str, matched: str = "") -> bool:
        """Is the match inside the scope of a negation?

        Scope stops at hard boundaries (; : dashes, brackets, 'but', 'however'...). A comma ends the
        scope too, unless the clause is a short list item ("I can't give tips, predict prices, guarantee
        returns"). The matched text itself takes part in that test, so "Don't worry, you will definitely
        make profits" stays a claim: its clause has a subject and a modal."""
        hard = _HARD_SPLIT.split(prefix)[-1]
        chosen = []
        for i, seg in enumerate(reversed(hard.split(","))):
            chosen.append(seg)
            if NEGATION.search(seg):
                break
            probe = seg + (" " + matched if i == 0 else "")
            if not _list_like(probe):
                break
        joined = " ".join(reversed(chosen))
        if len(chosen) > 1:
            joined = _IMPERATIVE_NEG.sub("", joined)
        return bool(NEGATION.search(" ".join(joined.split()[-14:])))


class ExternalClassifier(Protocol):
    """Optional second opinion (e.g. an LLM). It can only ADD matches, never clear one."""

    async def classify(self, text: str, ctx: ReviewContext) -> list: ...
