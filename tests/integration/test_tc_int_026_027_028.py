"""Integration tests for Slice 3 completion criteria.

TC-INT-026: Bad IFC data blocks BIR generation
TC-INT-028: bir_id bidirectional reference (round-trip)

Prerequisites: docker compose up (kg-store + kg-store-oxigraph)
Run:  pytest tests/integration/ -v
"""
import json
import os
import time

import pytest
import httpx

KG_STORE_URL = os.getenv("KG_STORE_URL", "http://localhost:8080")

pytestmark = pytest.mark.integration


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def http():
    with httpx.Client(base_url=KG_STORE_URL, timeout=10.0) as c:
        # Wait for service readiness
        for _ in range(20):
            try:
                r = c.get("/healthz")
                if r.status_code == 200:
                    break
            except Exception:
                pass
            time.sleep(1)
        yield c


# ── TC-INT-026: Bad IFC blocks BIR generation ─────────────────────────────────

class TestTC_INT_026:
    """TC-INT-026: bad IFC data must not reach the triplestore."""

    INVALID_KIND = """
    @prefix bir: <https://arch-pulse.example/ns/bir#> .
    @prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
    <urn:bir:INVALID:550e8400-e29b-41d4-a716-446655440000>
        a bir:Entity ;
        bir:status "Active"^^xsd:string .
    """

    MISSING_STATUS = """
    @prefix bir: <https://arch-pulse.example/ns/bir#> .
    <urn:bir:space:550e8400-e29b-41d4-a716-446655440099>
        a bir:Entity .
    """

    BAD_STATUS_VALUE = """
    @prefix bir: <https://arch-pulse.example/ns/bir#> .
    @prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
    <urn:bir:space:550e8400-e29b-41d4-a716-446655440098>
        a bir:Entity ;
        bir:status "PENDING"^^xsd:string .
    """

    DUPLICATE_IFC_GUID = """
    @prefix bir: <https://arch-pulse.example/ns/bir#> .
    @prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
    <urn:bir:space:550e8400-e29b-41d4-a716-446655440097>
        a bir:Entity ;
        bir:status "Active"^^xsd:string ;
        bir:hasIfcGuid "GUID-A" ;
        bir:hasIfcGuid "GUID-B" .
    """

    def test_invalid_kind_blocked(self, http):
        r = http.post("/bir/entities", content=self.INVALID_KIND,
                      headers={"Content-Type": "text/turtle"})
        assert r.status_code == 422, f"Expected 422, got {r.status_code}: {r.text}"

    def test_missing_status_blocked(self, http):
        r = http.post("/bir/entities", content=self.MISSING_STATUS,
                      headers={"Content-Type": "text/turtle"})
        assert r.status_code == 422, f"Expected 422, got {r.status_code}: {r.text}"

    def test_invalid_status_value_blocked(self, http):
        r = http.post("/bir/entities", content=self.BAD_STATUS_VALUE,
                      headers={"Content-Type": "text/turtle"})
        assert r.status_code == 422, f"Expected 422, got {r.status_code}: {r.text}"

    def test_duplicate_external_ref_blocked(self, http):
        r = http.post("/bir/entities", content=self.DUPLICATE_IFC_GUID,
                      headers={"Content-Type": "text/turtle"})
        assert r.status_code == 422, f"Expected 422, got {r.status_code}: {r.text}"

    def test_invalid_entity_not_in_store(self, http):
        """Confirm rejected entities are not queryable via SPARQL."""
        sparql = """
        ASK { <urn:bir:INVALID:550e8400-e29b-41d4-a716-446655440000> ?p ?o }
        """
        r = http.post("/sparql", content=sparql,
                      headers={"Content-Type": "application/sparql-query",
                               "Accept": "application/sparql-results+json"})
        assert r.status_code == 200
        data = r.json()
        assert data.get("boolean") is False, "Blocked entity must not appear in store"


# ── TC-INT-028: bir_id bidirectional reference ────────────────────────────────

class TestTC_INT_028:
    """TC-INT-028: bir_id round-trip — write entity, look up by every external ref."""

    SPACE_ENTITY = """
    @prefix bir: <https://arch-pulse.example/ns/bir#> .
    @prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

    <urn:bir:space:aaaabbbb-cccc-dddd-eeee-ffffffffffff>
        a bir:Entity ;
        bir:status "Active"^^xsd:string ;
        bir:hasIfcGuid "INT028_IFC_SPACE" ;
        bir:hasRevitElementId "INT028_REVIT_SPACE" ;
        bir:hasEnergyPlusZone "INT028_EPZ_SPACE" ;
        bir:hasBasPointPrefix "BLDG/INT028/" .
    """

    DEVICE_ENTITY = """
    @prefix bir: <https://arch-pulse.example/ns/bir#> .
    @prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

    <urn:bir:device:11112222-3333-4444-5555-666677778888>
        a bir:Entity ;
        bir:status "Active"^^xsd:string ;
        bir:hasIfcGuid "INT028_IFC_DEVICE" ;
        bir:hasBrickUri "https://brickschema.org/test#INT028_DEVICE" .
    """

    @pytest.fixture(scope="class", autouse=True)
    def write_entities(self, http):
        http.post("/bir/entities", content=self.SPACE_ENTITY,
                  headers={"Content-Type": "text/turtle"})
        http.post("/bir/entities", content=self.DEVICE_ENTITY,
                  headers={"Content-Type": "text/turtle"})

    def test_lookup_space_by_ifc_guid(self, http):
        r = http.get("/bir/lookup", params={"system": "ifc", "id": "INT028_IFC_SPACE"})
        assert r.status_code == 200
        data = r.json()
        assert data["bir_id"] == "urn:bir:space:aaaabbbb-cccc-dddd-eeee-ffffffffffff"
        assert data["kind"] == "space"

    def test_lookup_space_by_revit_id(self, http):
        r = http.get("/bir/lookup", params={"system": "revit", "id": "INT028_REVIT_SPACE"})
        assert r.status_code == 200
        assert r.json()["bir_id"] == "urn:bir:space:aaaabbbb-cccc-dddd-eeee-ffffffffffff"

    def test_lookup_space_by_energyplus_zone(self, http):
        r = http.get("/bir/lookup", params={"system": "energyplus", "id": "INT028_EPZ_SPACE"})
        assert r.status_code == 200
        assert "urn:bir:space" in r.json()["bir_id"]

    def test_lookup_device_by_ifc_guid(self, http):
        r = http.get("/bir/lookup", params={"system": "ifc", "id": "INT028_IFC_DEVICE"})
        assert r.status_code == 200
        data = r.json()
        assert data["bir_id"] == "urn:bir:device:11112222-3333-4444-5555-666677778888"
        assert data["kind"] == "device"

    def test_get_entity_by_bir_id(self, http):
        r = http.get("/bir/entities/urn:bir:space:aaaabbbb-cccc-dddd-eeee-ffffffffffff")
        assert r.status_code == 200
        assert "bir#Entity" in r.text or "bir:Entity" in r.text

    def test_sparql_query_by_ifc_guid(self, http):
        sparql = """
        PREFIX bir: <https://arch-pulse.example/ns/bir#>
        SELECT ?entity WHERE {
            ?entity bir:hasIfcGuid "INT028_IFC_SPACE" .
        }
        """
        r = http.post("/sparql", content=sparql,
                      headers={"Content-Type": "application/sparql-query",
                               "Accept": "application/sparql-results+json"})
        assert r.status_code == 200
        data = r.json()
        bindings = data["results"]["bindings"]
        assert len(bindings) == 1
        assert bindings[0]["entity"]["value"] == "urn:bir:space:aaaabbbb-cccc-dddd-eeee-ffffffffffff"
