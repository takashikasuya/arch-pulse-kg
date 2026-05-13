"""BIR CRUD and bidirectional lookup tests — verifies TC-INT-028 at component level.

TC-INT-028: bir_id bidirectional reference (external ID → bir_id, bir_id → entity).
"""
import pytest


SPACE_TURTLE = """
@prefix bir: <https://arch-pulse.example/ns/bir#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

<urn:bir:space:550e8400-e29b-41d4-a716-446655440000>
    a bir:Entity ;
    bir:status "Active"^^xsd:string ;
    bir:hasIfcGuid "3mXkZ9JyP9YgmW4eS_test1" ;
    bir:hasEnergyPlusZone "Zone_F01_A101" ;
    bir:hasBasPointPrefix "BLDG/F01/R101/" .
"""

DEVICE_TURTLE = """
@prefix bir: <https://arch-pulse.example/ns/bir#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

<urn:bir:device:6ba7b810-9dad-11d1-80b4-00c04fd430c8>
    a bir:Entity ;
    bir:status "Active"^^xsd:string ;
    bir:hasIfcGuid "DeviceIfcGuid_001" ;
    bir:hasRevitElementId "9876543" .
"""


@pytest.fixture()
def populated_client(client):
    client.post("/bir/entities", content=SPACE_TURTLE, headers={"Content-Type": "text/turtle"})
    client.post("/bir/entities", content=DEVICE_TURTLE, headers={"Content-Type": "text/turtle"})
    return client


def test_write_and_read_entity(populated_client):
    r = populated_client.get("/bir/entities/urn:bir:space:550e8400-e29b-41d4-a716-446655440000")
    assert r.status_code == 200
    assert "bir:Entity" in r.text or "bir#Entity" in r.text


def test_lookup_by_ifc_guid_space(populated_client):
    r = populated_client.get("/bir/lookup", params={"system": "ifc", "id": "3mXkZ9JyP9YgmW4eS_test1"})
    assert r.status_code == 200
    data = r.json()
    assert data["bir_id"] == "urn:bir:space:550e8400-e29b-41d4-a716-446655440000"
    assert data["kind"] == "space"
    assert data["status"] == "Active"


def test_lookup_by_ifc_guid_device(populated_client):
    r = populated_client.get("/bir/lookup", params={"system": "ifc", "id": "DeviceIfcGuid_001"})
    assert r.status_code == 200
    data = r.json()
    assert data["bir_id"] == "urn:bir:device:6ba7b810-9dad-11d1-80b4-00c04fd430c8"
    assert data["kind"] == "device"


def test_lookup_by_revit_id(populated_client):
    r = populated_client.get("/bir/lookup", params={"system": "revit", "id": "9876543"})
    assert r.status_code == 200
    data = r.json()
    assert data["bir_id"] == "urn:bir:device:6ba7b810-9dad-11d1-80b4-00c04fd430c8"


def test_lookup_by_energyplus_zone(populated_client):
    r = populated_client.get("/bir/lookup", params={"system": "energyplus", "id": "Zone_F01_A101"})
    assert r.status_code == 200
    data = r.json()
    assert "urn:bir:space" in data["bir_id"]


def test_lookup_nonexistent_returns_404(populated_client):
    r = populated_client.get("/bir/lookup", params={"system": "ifc", "id": "no-such-guid"})
    assert r.status_code == 404


def test_lookup_unknown_system_returns_400(populated_client):
    r = populated_client.get("/bir/lookup", params={"system": "sap", "id": "anything"})
    assert r.status_code == 400


def test_get_nonexistent_entity_returns_404(populated_client):
    r = populated_client.get("/bir/entities/urn:bir:space:ffffffff-ffff-ffff-ffff-ffffffffffff")
    assert r.status_code == 404


def test_nats_event_published_on_write(client, null_pub):
    client.post("/bir/entities", content=SPACE_TURTLE, headers={"Content-Type": "text/turtle"})
    assert len(null_pub.published) == 1
    evt = null_pub.published[0]
    assert evt["bir_id"] == "urn:bir:space:550e8400-e29b-41d4-a716-446655440000"
    assert len(evt["added"]) > 0


def test_update_entity_diff_on_second_write(client, null_pub):
    client.post("/bir/entities", content=SPACE_TURTLE, headers={"Content-Type": "text/turtle"})
    first_count = len(null_pub.published[0]["added"])

    updated = SPACE_TURTLE.replace("Active", "Archived")
    client.post("/bir/entities", content=updated, headers={"Content-Type": "text/turtle"})
    assert len(null_pub.published) == 2
    second = null_pub.published[1]
    assert len(second["added"]) > 0 or len(second["removed"]) > 0
