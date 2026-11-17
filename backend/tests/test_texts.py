"""Every static string the bot can send must itself pass the compliance gate."""
from types import SimpleNamespace

from app.bot import texts
from app.compliance.compliance_engine import ComplianceEngine
from app.compliance.compliance_models import Severity

E = ComplianceEngine()


def test_all_static_texts_pass_the_gate():
    bad = []
    for name in dir(texts):
        v = getattr(texts, name)
        if name.isupper() and isinstance(v, str):
            v = v.replace("{code}", "TM-ABC234")
            hits = [m.rule_id for m in E.scan(v) if m.severity >= Severity.MEDIUM]
            if hits:
                bad.append((name, hits))
    p = SimpleNamespace(has_traded=False, experience="beginner", learning_capital=50000,
                        objectives="Understand risk", language="English")
    bad += [("profile_text", [m.rule_id for m in E.scan(texts.profile_text(p)) if m.severity >= Severity.MEDIUM])]
    bad = [b for b in bad if b[1]]
    assert not bad, bad


def test_list_negation_does_not_hide_claims():
    for t in ["I can't give tips, predict prices, guarantee returns, or place trades.",
              "I won't predict prices, promise profits or guarantee returns."]:
        assert not [m for m in E.scan(t) if m.severity >= Severity.MEDIUM], t
    for t in ["Don't worry, you will definitely make profits.",
              "I can't predict the market, but this plan guarantees returns."]:
        assert [m for m in E.scan(t) if m.severity >= Severity.MEDIUM], t
