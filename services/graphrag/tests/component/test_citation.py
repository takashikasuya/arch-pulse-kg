"""Unit tests for citation domain logic — REQ-SOS-022."""
from graphrag.domain.models import CausalPath, CitationNode, Period
from graphrag.domain.citation import (
    make_citation, build_assertion_citation_map, build_evidence_payload,
)

_PERIOD = Period(start="2024-01-01T00:00:00Z", end="2024-01-31T23:59:59Z")
_BIR_ID = "urn:bir:space:550e8400-e29b-41d4-a716-446655440000"


def test_citation_id_is_unique_per_call():
    c1 = make_citation(_BIR_ID, "bir:contains", "urn:bir:device:...", _PERIOD)
    c2 = make_citation(_BIR_ID, "bir:contains", "urn:bir:device:...", _PERIOD)
    assert c1.citation_id != c2.citation_id


def test_citation_source_is_if_kg_001():
    c = make_citation(_BIR_ID, "bir:hasPoint", "urn:bir:point:...", _PERIOD)
    assert c.source == "IF-KG-001"


def test_all_path_citations_in_citation_list():
    c1 = make_citation(_BIR_ID, "bir:contains", "urn:bir:device:...", _PERIOD)
    c2 = make_citation(_BIR_ID, "bir:hasPoint", "urn:bir:point:...", _PERIOD)
    path = CausalPath(
        path_id="p1",
        nodes=[_BIR_ID, "urn:bir:device:..."],
        predicates=["bir:contains"],
        citation_ids=[c1.citation_id, c2.citation_id],
    )
    citations = [c1, c2]
    acm = build_assertion_citation_map([path], citations)
    for cid in acm.values():
        assert any(c.citation_id == cid for c in citations)


def test_evidence_payload_structure():
    c = make_citation(_BIR_ID, "bir:contains", "urn:bir:device:...", _PERIOD)
    path = CausalPath(
        path_id="p1",
        nodes=[_BIR_ID, "urn:bir:device:..."],
        predicates=["bir:contains"],
        citation_ids=[c.citation_id],
    )
    acm = build_assertion_citation_map([path], [c])
    payload = build_evidence_payload("question?", [path], [c], acm)
    assert "citations" in payload
    assert "causal_paths" in payload
    assert "assertion_citation_map" in payload
    assert payload["question"] == "question?"
