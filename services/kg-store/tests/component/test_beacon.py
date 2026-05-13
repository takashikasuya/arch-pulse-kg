"""Component tests for bir:Beacon registration and beacon_id → bir_id lookup (Issue #1)."""

BEACON_TURTLE = """
@prefix bir: <https://arch-pulse.example/ns/bir#> .

<urn:beacon:f2-east-001> a bir:Beacon ;
    bir:locatedIn <urn:bir:space:550e8400-e29b-41d4-a716-446655440000> ;
    bir:beaconProtocol "BLE" ;
    bir:floor "F2" .
"""

BEACON_MISSING_LOCATED_IN = """
@prefix bir: <https://arch-pulse.example/ns/bir#> .

<urn:beacon:f2-east-002> a bir:Beacon ;
    bir:beaconProtocol "BLE" .
"""

BEACON_BAD_IRI = """
@prefix bir: <https://arch-pulse.example/ns/bir#> .

<urn:beacon:> a bir:Beacon ;
    bir:locatedIn <urn:bir:space:550e8400-e29b-41d4-a716-446655440000> .
"""

BEACON_DUPLICATE_LOCATED_IN = """
@prefix bir: <https://arch-pulse.example/ns/bir#> .

<urn:beacon:f2-east-003> a bir:Beacon ;
    bir:locatedIn <urn:bir:space:550e8400-e29b-41d4-a716-446655440000> ;
    bir:locatedIn <urn:bir:space:660f9511-f3ac-52e5-b827-557766551111> .
"""


def test_write_beacon_returns_201(client):
    r = client.post("/bir/beacons", content=BEACON_TURTLE,
                    headers={"Content-Type": "text/turtle"})
    assert r.status_code == 201, r.text
    data = r.json()
    assert data["beacon_id"] == "urn:beacon:f2-east-001"
    assert data["status"] == "written"


def test_write_beacon_missing_located_in_rejected(client):
    r = client.post("/bir/beacons", content=BEACON_MISSING_LOCATED_IN,
                    headers={"Content-Type": "text/turtle"})
    assert r.status_code == 422, r.text


def test_write_beacon_bad_iri_pattern_rejected(client):
    r = client.post("/bir/beacons", content=BEACON_BAD_IRI,
                    headers={"Content-Type": "text/turtle"})
    assert r.status_code == 422, r.text


def test_write_beacon_duplicate_located_in_rejected(client):
    r = client.post("/bir/beacons", content=BEACON_DUPLICATE_LOCATED_IN,
                    headers={"Content-Type": "text/turtle"})
    assert r.status_code == 422, r.text


def test_beacon_lookup_returns_bir_id(client):
    client.post("/bir/beacons", content=BEACON_TURTLE,
                headers={"Content-Type": "text/turtle"})
    r = client.get("/bir/beacon-lookup", params={"beacon_id": "urn:beacon:f2-east-001"})
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["beacon_id"] == "urn:beacon:f2-east-001"
    assert data["bir_id"] == "urn:bir:space:550e8400-e29b-41d4-a716-446655440000"
    assert data["kind"] == "space"


def test_beacon_lookup_not_registered_returns_404(client):
    r = client.get("/bir/beacon-lookup", params={"beacon_id": "urn:beacon:nonexistent"})
    assert r.status_code == 404, r.text


def test_beacon_lookup_invalid_id_format_returns_400(client):
    r = client.get("/bir/beacon-lookup", params={"beacon_id": "not-a-beacon-urn"})
    assert r.status_code == 400, r.text


def test_write_beacon_is_idempotent(client):
    r1 = client.post("/bir/beacons", content=BEACON_TURTLE,
                     headers={"Content-Type": "text/turtle"})
    assert r1.status_code == 201

    r2 = client.post("/bir/beacons", content=BEACON_TURTLE,
                     headers={"Content-Type": "text/turtle"})
    assert r2.status_code == 201

    r = client.get("/bir/beacon-lookup", params={"beacon_id": "urn:beacon:f2-east-001"})
    assert r.status_code == 200
    assert r.json()["bir_id"] == "urn:bir:space:550e8400-e29b-41d4-a716-446655440000"


def test_write_beacon_does_not_publish_nats_event(client, null_pub):
    client.post("/bir/beacons", content=BEACON_TURTLE,
                headers={"Content-Type": "text/turtle"})
    assert len(null_pub.published) == 0
