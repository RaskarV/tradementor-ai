from app.compliance.compliance_engine import ComplianceEngine
from app.compliance.compliance_models import Severity
from app.knowledge.document_processor import chunk_text, find_injection, sanitize_document
from app.knowledge.seed_content import SEED_DOCS
from app.knowledge.topics import TOPICS


def test_seed_covers_all_topics_and_is_clean():
    assert set(SEED_DOCS) == {s for s, _ in TOPICS} and len(TOPICS) == 16
    e = ComplianceEngine()
    for slug, body in SEED_DOCS.items():
        assert not find_injection(body), slug
        assert sanitize_document(body) == body.strip(), slug
        hits = [m.rule_id for m in e.scan(body) if m.severity >= Severity.MEDIUM]
        assert not hits, (slug, hits)
        assert chunk_text(body), slug
