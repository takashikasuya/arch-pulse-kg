"""Component tests for causal analysis endpoint — TC-COMP-AI-GRAPHRAG-001."""
from .conftest import SPACE_BIR_ID

VALID_REQUEST = {
    "tenant_id": "urn:bir:tenant:00000000-0000-0000-0000-000000000000",
    "context_bir_id": SPACE_BIR_ID,
    "period": {"start": "2024-01-01T00:00:00Z", "end": "2024-01-31T23:59:59Z"},
    "question": "Why did energy consumption increase?",
}


def test_causal_analysis_returns_200(client):
    r = client.post("/analysis/causal", json=VALID_REQUEST)
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["context_bir_id"] == SPACE_BIR_ID
    assert len(data["causal_paths"]) > 0


def test_assertion_citation_map_is_bijective(client):
    """TC-INT-022: every assertion must map to exactly one citation."""
    r = client.post("/analysis/causal", json=VALID_REQUEST)
    assert r.status_code == 200
    data = r.json()
    acm = data["assertion_citation_map"]
    citation_ids = {c["citation_id"] for c in data["citations"]}
    # Every value in the map must exist in citations
    for assertion_key, cid in acm.items():
        assert cid in citation_ids, f"Citation {cid} missing for assertion {assertion_key}"
    # No duplicate citation references (1:1)
    assert len(set(acm.values())) == len(acm.values())


def test_empty_kg_returns_empty_paths(empty_client):
    r = empty_client.post("/analysis/causal", json=VALID_REQUEST)
    assert r.status_code == 200
    data = r.json()
    assert data["causal_paths"] == []
    assert data["citations"] == []


def test_invalid_bir_id_returns_422(client):
    bad_request = {**VALID_REQUEST, "context_bir_id": "not-a-bir-id"}
    r = client.post("/analysis/causal", json=bad_request)
    assert r.status_code == 422, r.text


def test_evidence_payload_contains_citations(client):
    r = client.post("/analysis/causal", json=VALID_REQUEST)
    assert r.status_code == 200
    data = r.json()
    payload = data["evidence_payload"]
    assert "citations" in payload
    assert "causal_paths" in payload
    assert "question" in payload
    assert "assertion_citation_map" in payload
