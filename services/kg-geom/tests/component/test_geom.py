"""Component tests for CS-KG-GEOM IF-KG-002 endpoints (#12, REQ-SOS-005/026)."""

TENANT_A = "urn:bir:tenant:aaaaaaaa-0000-0000-0000-000000000001"
TENANT_B = "urn:bir:tenant:bbbbbbbb-0000-0000-0000-000000000002"

_POLY_BIR_ID = "urn:bir:geometry:11111111-1111-1111-1111-111111111111"
_POLY_UUID = "11111111-1111-1111-1111-111111111111"
_SPACE_BIR_ID = "urn:bir:space:22222222-2222-2222-2222-222222222222"

_SQUARE_POLYGON = {
    "type": "Polygon",
    "coordinates": [[[0.0, 0.0], [10.0, 0.0], [10.0, 10.0], [0.0, 10.0], [0.0, 0.0]]],
}

_NEAR_BIR_ID = "urn:bir:geometry:33333333-3333-3333-3333-333333333333"
_NEAR_UUID = "33333333-3333-3333-3333-333333333333"
_FAR_BIR_ID = "urn:bir:geometry:44444444-4444-4444-4444-444444444444"
_FAR_UUID = "44444444-4444-4444-4444-444444444444"

_TENANT_B_BIR_ID = "urn:bir:geometry:55555555-5555-5555-5555-555555555555"


def _write_polygon(client, bir_id=_POLY_BIR_ID, tid=TENANT_A, space_bir_id=_SPACE_BIR_ID):
    return client.post(
        "/geom/write",
        json={
            "bir_id": bir_id,
            "tid": tid,
            "geom_type": "polygon",
            "geom": _SQUARE_POLYGON,
            "altitude_m": 0.0,
            "space_bir_id": space_bir_id,
        },
    )


def _write_point(client, bir_id, tid, x, y):
    return client.post(
        "/geom/write",
        json={
            "bir_id": bir_id,
            "tid": tid,
            "geom_type": "point",
            "geom": {"type": "Point", "coordinates": [x, y]},
            "altitude_m": 0.0,
        },
    )


def test_write_and_get_geometry(client):
    """POST /geom/write → 201; GET /geom/{uuid} → 200 + ETag (IF-KG-002)."""
    r = _write_polygon(client)
    assert r.status_code == 201, r.text

    r = client.get(f"/geom/{_POLY_UUID}", params={"tid": TENANT_A})
    assert r.status_code == 200, r.text
    assert "ETag" in r.headers
    assert r.json()["type"] == "Polygon"


def test_head_returns_etag(client):
    """HEAD /geom/{uuid} returns ETag without body (IF-KG-002)."""
    _write_polygon(client)
    r = client.head(f"/geom/{_POLY_UUID}", params={"tid": TENANT_A})
    assert r.status_code == 200
    assert "ETag" in r.headers


def test_lookup_space_by_point_hit(client):
    """Point inside polygon returns the associated space bir_id (IF-KG-002)."""
    _write_polygon(client)
    r = client.get("/geom/lookup/space", params={"tid": TENANT_A, "x": 5.0, "y": 5.0, "z": 1.0})
    assert r.status_code == 200, r.text
    assert r.json()["bir_id"] == _SPACE_BIR_ID


def test_lookup_space_by_point_miss(client):
    """Point outside all polygons returns 404."""
    _write_polygon(client)
    r = client.get("/geom/lookup/space", params={"tid": TENANT_A, "x": 999.0, "y": 999.0, "z": 0.0})
    assert r.status_code == 404


def test_nearby_assets(client):
    """Assets within radius_m are returned; distant assets are excluded."""
    _write_point(client, _NEAR_BIR_ID, TENANT_A, x=5.0, y=5.0)
    _write_point(client, _FAR_BIR_ID, TENANT_A, x=500.0, y=500.0)

    r = client.get(
        "/geom/lookup/nearby",
        params={"tid": TENANT_A, "x": 5.0, "y": 5.0, "z": 0.0, "radius_m": 10.0},
    )
    assert r.status_code == 200, r.text
    bir_ids = [a["bir_id"] for a in r.json()["assets"]]
    assert _NEAR_BIR_ID in bir_ids
    assert _FAR_BIR_ID not in bir_ids


def test_geom_tenant_isolation(client):
    """Assets from TENANT_B are not visible to TENANT_A queries (REQ-SOS-005)."""
    _write_point(client, _TENANT_B_BIR_ID, TENANT_B, x=5.0, y=5.0)

    r = client.get(
        "/geom/lookup/nearby",
        params={"tid": TENANT_A, "x": 5.0, "y": 5.0, "z": 0.0, "radius_m": 1000.0},
    )
    assert r.status_code == 200
    bir_ids = [a["bir_id"] for a in r.json()["assets"]]
    assert _TENANT_B_BIR_ID not in bir_ids


def test_unknown_uuid_returns_404(client):
    """GET /geom/{uuid} for unknown UUID returns 404."""
    r = client.get("/geom/ffffffff-ffff-ffff-ffff-ffffffffffff", params={"tid": TENANT_A})
    assert r.status_code == 404


def test_invalid_tenant_returns_422(client):
    """Malformed tenant_id returns 422."""
    r = client.get("/geom/lookup/space", params={"tid": "not-a-tenant", "x": 0.0, "y": 0.0})
    assert r.status_code == 422
