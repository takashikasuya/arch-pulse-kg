"""SHACL validation gate tests — verifies TC-INT-026 at component level.

TC-INT-026: Bad IFC data must be blocked before BIR is written.
"""

# ── Valid entity fixtures ────────────────────────────────────────────────────

VALID_SPACE = """
@prefix bir: <https://arch-pulse.example/ns/bir#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

<urn:bir:space:550e8400-e29b-41d4-a716-446655440000>
    a bir:Entity ;
    bir:status "Active"^^xsd:string ;
    bir:hasIfcGuid "3mXkZ9JyP9YgmW4eS_xxxx" .
"""

VALID_DEVICE_WITH_REVIT = """
@prefix bir: <https://arch-pulse.example/ns/bir#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

<urn:bir:device:6ba7b810-9dad-11d1-80b4-00c04fd430c8>
    a bir:Entity ;
    bir:status "Draft"^^xsd:string ;
    bir:hasRevitElementId "456789" ;
    bir:hasEnergyPlusZone "Zone_F02_101" .
"""

# ── Invalid entity fixtures (must be rejected 422) ────────────────────────────

BAD_IRI_UPPERCASE_KIND = """
@prefix bir: <https://arch-pulse.example/ns/bir#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

<urn:bir:SPACE:550e8400-e29b-41d4-a716-446655440000>
    a bir:Entity ;
    bir:status "Active"^^xsd:string .
"""

BAD_IRI_UNKNOWN_KIND = """
@prefix bir: <https://arch-pulse.example/ns/bir#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

<urn:bir:unknown:550e8400-e29b-41d4-a716-446655440000>
    a bir:Entity ;
    bir:status "Active"^^xsd:string .
"""

BAD_STATUS_MISSING = """
@prefix bir: <https://arch-pulse.example/ns/bir#> .

<urn:bir:space:550e8400-e29b-41d4-a716-446655440001>
    a bir:Entity .
"""

BAD_STATUS_INVALID_VALUE = """
@prefix bir: <https://arch-pulse.example/ns/bir#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

<urn:bir:space:550e8400-e29b-41d4-a716-446655440002>
    a bir:Entity ;
    bir:status "RUNNING"^^xsd:string .
"""

BAD_IFC_GUID_DUPLICATE = """
@prefix bir: <https://arch-pulse.example/ns/bir#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

<urn:bir:space:550e8400-e29b-41d4-a716-446655440003>
    a bir:Entity ;
    bir:status "Active"^^xsd:string ;
    bir:hasIfcGuid "GUID-A" ;
    bir:hasIfcGuid "GUID-B" .
"""


# ── Tests ────────────────────────────────────────────────────────────────────

def test_valid_space_accepted(client):
    r = client.post(
        "/bir/entities", content=VALID_SPACE, headers={"Content-Type": "text/turtle"}
    )
    assert r.status_code == 201, r.text


def test_valid_device_accepted(client):
    r = client.post(
        "/bir/entities", content=VALID_DEVICE_WITH_REVIT, headers={"Content-Type": "text/turtle"}
    )
    assert r.status_code == 201, r.text


def test_bad_iri_uppercase_kind_rejected(client):
    r = client.post(
        "/bir/entities", content=BAD_IRI_UPPERCASE_KIND, headers={"Content-Type": "text/turtle"}
    )
    assert r.status_code == 422, r.text


def test_bad_iri_unknown_kind_rejected(client):
    r = client.post(
        "/bir/entities", content=BAD_IRI_UNKNOWN_KIND, headers={"Content-Type": "text/turtle"}
    )
    assert r.status_code == 422, r.text


def test_missing_status_rejected(client):
    r = client.post(
        "/bir/entities", content=BAD_STATUS_MISSING, headers={"Content-Type": "text/turtle"}
    )
    assert r.status_code == 422, r.text


def test_invalid_status_value_rejected(client):
    r = client.post(
        "/bir/entities", content=BAD_STATUS_INVALID_VALUE, headers={"Content-Type": "text/turtle"}
    )
    assert r.status_code == 422, r.text


def test_duplicate_ifc_guid_rejected(client):
    r = client.post(
        "/bir/entities", content=BAD_IFC_GUID_DUPLICATE, headers={"Content-Type": "text/turtle"}
    )
    assert r.status_code == 422, r.text
