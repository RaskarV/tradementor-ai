"""Data structures for the compliance gate. Standard library only (no AI/DB imports)."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, IntEnum


class Verdict(str, Enum):
    CLEARED = "cleared"
    BLOCKED = "blocked"


class Severity(IntEnum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

    @classmethod
    def parse(cls, value) -> "Severity":
        if isinstance(value, cls):
            return value
        return cls[str(value).strip().upper()]


@dataclass(frozen=True)
class RuleMatch:
    rule_id: str
    category: str
    severity: Severity
    excerpt: str
    source: str = "regex"  # regex | external


@dataclass(frozen=True)
class CustomRule:
    """Administrator-configured pattern. Never dismissed by context."""
    rule_id: str
    pattern: str
    severity: Severity = Severity.HIGH
    category: str = "custom"


@dataclass(frozen=True)
class CompliancePolicy:
    block_threshold: Severity = Severity.MEDIUM
    disabled_rules: frozenset = frozenset()
    severity_overrides: dict = field(default_factory=dict)  # rule_id -> Severity
    custom_rules: tuple = ()
    regulatory_phrases: tuple = ()
    external_required: bool = False


@dataclass(frozen=True)
class ReviewContext:
    """Facts supplied by the caller, never by the AI draft itself."""
    retrieved_text: str = ""  # knowledge-base text the draft was grounded on


@dataclass(frozen=True)
class ComplianceResult:
    verdict: Verdict
    final_text: str
    original_text: str
    matches: tuple = ()
    message_type: str = "reply"
    used_safe_alternative: bool = False

    @property
    def blocked(self) -> bool:
        return self.verdict is Verdict.BLOCKED

    @property
    def matched_rules(self) -> list:
        seen: list = []
        for m in self.matches:
            if m.rule_id not in seen:
                seen.append(m.rule_id)
        return seen

    @property
    def severity(self):
        return max((m.severity for m in self.matches), default=None)

    @property
    def excerpt(self):
        return self.matches[0].excerpt if self.matches else None
