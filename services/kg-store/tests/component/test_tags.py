"""Component tests for IF-KG-TAGSEARCH (REQ-SOS-060, REQ-SOS-061, FUN-KG-003)."""

TENANT_A = "urn:bir:tenant:aaaaaaaa-0000-0000-0000-000000000001"
TENANT_B = "urn:bir:tenant:bbbbbbbb-0000-0000-0000-000000000002"

DEVICE_WITH_TAGS = f"""
@prefix bir: <https://arch-pulse.example/ns/bir#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
<urn:bir:device:11111111-1111-1111-1111-111111111111>
    a bir:Entity ;
    bir:status "Active"^^xsd:string ;
    bir:tenantScope <{TENANT_A}> ;
    bir:customTag "haystack:hvac"^^xsd:string ;
    bir:customTag "bldg:dr-level-1"^^xsd:string .
"""

DEVICE_ONLY_HVAC = f"""
@prefix bir: <https://arch-pulse.example/ns/bir#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
<urn:bir:device:22222222-2222-2222-2222-222222222222>
    a bir:Entity ;
    bir:status "Active"^^xsd:string ;
    bir:tenantScope <{TENANT_A}> ;
    bir:customTag "haystack:hvac"^^xsd:string .
"""

DEVICE_OTHER_TENANT = f"""
@prefix bir: <https://arch-pulse.example/ns/bir#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
<urn:bir:device:33333333-3333-3333-3333-333333333333>
    a bir:Entity ;
    bir:status "Active"^^xsd:string ;
    bir:tenantScope <{TENANT_B}> ;
    bir:customTag "haystack:hvac"^^xsd:string .
"""

DEVICE_WITH_CTRL_TEMPLATE = f"""
@prefix bir: <https://arch-pulse.example/ns/bir#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
<urn:bir:device:44444444-4444-4444-4444-444444444444>
    a bir:Entity ;
    bir:status "Active"^^xsd:string ;
    bir:tenantScope <{TENANT_A}> ;
    bir:customTag "haystack:chiller"^^xsd:string ;
    bir:hasControlTemplate "urn:bir:ctrl-seq:cccccccc-cccc-cccc-cccc-cccccccccccc"^^xsd:string .
"""

DEVICE_BLDG_TAG = f"""
@prefix bir: <https://arch-pulse.example/ns/bir#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
<urn:bir:device:55555555-5555-5555-5555-555555555555>
    a bir:Entity ;
    bir:status "Active"^^xsd:string ;
    bir:tenantScope <{TENANT_A}> ;
    bir:customTag "bldg:custom-zone"^^xsd:string .
"""

DEVICE_UNKNOWN_HAYSTACK_TAG = f"""
@prefix bir: <https://arch-pulse.example/ns/bir#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
<urn:bir:device:66666666-6666-6666-6666-666666666666>
    a bir:Entity ;
    bir:status "Active"^^xsd:string ;
    bir:tenantScope <{TENANT_A}> ;
    bir:customTag "haystack:nonexistent-unknown-xyz"^^xsd:string .
"""

_HEADERS = {"Content-Type": "text/turtle"}


def _write(client, turtle: str) -> int:
    return client.post("/bir/entities", content=turtle, headers=_HEADERS).status_code


def test_tag_search_returns_matching_entity(client):
    """Single tag search returns the entity that has that tag (REQ-SOS-060)."""
    assert _write(client, DEVICE_WITH_TAGS) == 201

    r = client.get("/tags/search", params={"tags": "haystack:hvac", "tenant_id": TENANT_A})
    assert r.status_code == 200, r.text
    data = r.json()
    bir_ids = [res["bir_id"] for res in data["results"]]
    assert "urn:bir:device:11111111-1111-1111-1111-111111111111" in bir_ids
    assert data["count"] >= 1


def test_tag_search_and_logic(client):
    """AND logic: only entities with ALL requested tags are returned."""
    assert _write(client, DEVICE_WITH_TAGS) == 201    # has both hvac + bldg:dr-level-1
    assert _write(client, DEVICE_ONLY_HVAC) == 201    # has only hvac

    r = client.get(
        "/tags/search",
        params=[("tags", "haystack:hvac"), ("tags", "bldg:dr-level-1"), ("tenant_id", TENANT_A)],
    )
    assert r.status_code == 200, r.text
    bir_ids = [res["bir_id"] for res in r.json()["results"]]
    assert "urn:bir:device:11111111-1111-1111-1111-111111111111" in bir_ids
    assert "urn:bir:device:22222222-2222-2222-2222-222222222222" not in bir_ids


def test_tag_search_tenant_isolation(client):
    """Entity from a different tenant must not appear in results (REQ-SOS-061)."""
    assert _write(client, DEVICE_WITH_TAGS) == 201        # TENANT_A
    assert _write(client, DEVICE_OTHER_TENANT) == 201     # TENANT_B, same tag

    r = client.get("/tags/search", params={"tags": "haystack:hvac", "tenant_id": TENANT_A})
    assert r.status_code == 200, r.text
    bir_ids = [res["bir_id"] for res in r.json()["results"]]
    assert "urn:bir:device:33333333-3333-3333-3333-333333333333" not in bir_ids


def test_tag_search_returns_ctrl_template(client):
    """control_template_id is included when bir:hasControlTemplate is set."""
    assert _write(client, DEVICE_WITH_CTRL_TEMPLATE) == 201

    r = client.get("/tags/search", params={"tags": "haystack:chiller", "tenant_id": TENANT_A})
    assert r.status_code == 200, r.text
    results = r.json()["results"]
    assert len(results) == 1
    assert results[0]["control_template_id"] == "urn:bir:ctrl-seq:cccccccc-cccc-cccc-cccc-cccccccccccc"


def test_tag_search_no_match_returns_empty(client):
    """No matching entities returns empty results list with 200."""
    r = client.get("/tags/search", params={"tags": "haystack:boiler", "tenant_id": TENANT_A})
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["results"] == []
    assert data["count"] == 0


def test_unknown_haystack_tag_write_rejected(client):
    """Writing an entity with an unregistered haystack: tag must return 422 (7-c)."""
    r = client.post("/bir/entities", content=DEVICE_UNKNOWN_HAYSTACK_TAG, headers=_HEADERS)
    assert r.status_code == 422, r.text
    data = r.json()
    assert "invalid_tags" in data.get("detail", data)


def test_bldg_tag_write_accepted(client):
    """bldg: prefixed tags are free-form and must be accepted (ADR-021)."""
    r = client.post("/bir/entities", content=DEVICE_BLDG_TAG, headers=_HEADERS)
    assert r.status_code == 201, r.text


def test_tag_search_invalid_tenant_returns_422(client):
    """Malformed tenant_id must return 422."""
    r = client.get(
        "/tags/search",
        params={"tags": "haystack:hvac", "tenant_id": "not-a-valid-tenant"},
    )
    assert r.status_code == 422, r.text
