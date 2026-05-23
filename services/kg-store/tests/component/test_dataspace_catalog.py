"""Component tests for GET /dataspace/catalog (REQ-SOS-056, TC-COMP-KG-STORE-003)."""
import json
import jwt
import pytest

TENANT_A = "urn:bir:tenant:aaaaaaaa-0000-0000-0000-000000000001"
_SECRET = "test-secret-replace-in-prod-min32b"

_TUNNEL_HEADERS = {"x-tunnel-source": "cloud-dsc"}

_DS_EXPOSED = {
    "dataset_uri": "urn:archpulse:dataset:exposed-001",
    "tenant_scope": TENANT_A,
    "data_class": "Analytics",
    "opt_in_job_id": "job-001",
    "period": {"start": "2026-01-01", "end": "2026-01-31"},
    "byte_size": 1024,
    "checksum": {"algorithm": "sha256", "value": "abc123"},
    "was_derived_from": "urn:archpulse:source:sensor-stream",
    "exposed": True,
    "access_url": "https://storage.example/dataset-001.parquet",
    "media_type": "application/vnd.apache.parquet",
}

_DS_HIDDEN = {
    "dataset_uri": "urn:archpulse:dataset:hidden-001",
    "tenant_scope": TENANT_A,
    "data_class": "Sovereign",
    "opt_in_job_id": "job-002",
    "period": {"start": "2026-01-01", "end": "2026-01-31"},
    "byte_size": 512,
    "checksum": {"algorithm": "sha256", "value": "def456"},
    "was_derived_from": "urn:archpulse:source:sensor-stream",
    "exposed": False,
}


def _make_jwt(tenant_id: str = TENANT_A) -> str:
    return jwt.encode({"tenant_id": tenant_id, "sub": "cloud-dsc"}, _SECRET, algorithm="HS256")


def _register_dataset(client, ds: dict) -> None:
    r = client.post("/catalog/datasets", json=ds)
    assert r.status_code == 201, r.text


def test_direct_access_rejected(client):
    """Missing x-tunnel-source header returns 403 (ADR-026 structural enforcement)."""
    token = _make_jwt()
    r = client.get("/dataspace/catalog", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 403


def test_missing_jwt_rejected(client):
    """Tunnel header present but no Bearer token returns 401."""
    r = client.get("/dataspace/catalog", headers=_TUNNEL_HEADERS)
    assert r.status_code == 401


def test_jsonld_response(client):
    """Valid tunnel + JWT with Accept: application/ld+json returns JSON-LD."""
    _register_dataset(client, _DS_EXPOSED)
    token = _make_jwt()
    r = client.get(
        "/dataspace/catalog",
        headers={**_TUNNEL_HEADERS, "Authorization": f"Bearer {token}", "Accept": "application/ld+json"},
    )
    assert r.status_code == 200, r.text
    assert "application/ld+json" in r.headers["content-type"]
    body = r.json()
    assert isinstance(body, (dict, list))


def test_turtle_response(client):
    """Valid tunnel + JWT with Accept: text/turtle returns Turtle RDF."""
    _register_dataset(client, _DS_EXPOSED)
    token = _make_jwt()
    r = client.get(
        "/dataspace/catalog",
        headers={**_TUNNEL_HEADERS, "Authorization": f"Bearer {token}", "Accept": "text/turtle"},
    )
    assert r.status_code == 200, r.text
    assert "text/turtle" in r.headers["content-type"]
    assert "Dataset" in r.text


def test_exposed_only_filtered(client):
    """Datasets with exposed=False are excluded from /dataspace/catalog."""
    _register_dataset(client, _DS_EXPOSED)
    _register_dataset(client, _DS_HIDDEN)
    token = _make_jwt()
    r = client.get(
        "/dataspace/catalog",
        headers={**_TUNNEL_HEADERS, "Authorization": f"Bearer {token}", "Accept": "text/turtle"},
    )
    assert r.status_code == 200, r.text
    assert _DS_EXPOSED["dataset_uri"] in r.text
    assert _DS_HIDDEN["dataset_uri"] not in r.text


def test_catalog_datasets_jsonld_negotiation(client):
    """Existing /catalog/datasets with Accept: application/ld+json returns JSON-LD (backwards compat)."""
    _register_dataset(client, _DS_EXPOSED)
    r = client.get("/catalog/datasets", headers={"Accept": "application/ld+json"})
    assert r.status_code == 200, r.text
    assert "application/ld+json" in r.headers["content-type"]
    body = r.json()
    assert isinstance(body, (dict, list))
