"""Component tests for BIR mapping and load pipeline (#11, REQ-SOS-028/032)."""
from kg_bim_loader.domain.ifc_model import IfcEntity, Face
from kg_bim_loader.adapters.mock_ifc_parser import MockIfcParser
from kg_bim_loader.adapters.in_memory_kg_store import InMemoryKgStorePort
from kg_bim_loader.adapters.null_publisher import NullPublisher
from kg_bim_loader.services.bim_load_pipeline import BimLoadPipeline

TENANT_A = "urn:bir:tenant:aaaaaaaa-0000-0000-0000-000000000001"

_SPACE_GUID = "1234567890ABCDEFGHIJK0"
_AHU_GUID = "AAAAABBBBBCCCCCDDDDDE0"


def _good_space() -> IfcEntity:
    return IfcEntity(
        ifc_guid=_SPACE_GUID,
        ifc_class="IfcSpace",
        name="Meeting Room",
        faces=[Face(area=10.0, normal=(0.0, 0.0, 1.0))],
        pset_values={"Pset_SpaceCommon": {"IsExternal": "false", "GrossFloorArea": "45.2"}},
    )


def _good_ahu() -> IfcEntity:
    return IfcEntity(
        ifc_guid=_AHU_GUID,
        ifc_class="IfcAirHandlingUnit",
        name="AHU-01",
        faces=[Face(area=2.0, normal=(0.0, 1.0, 0.0))],
        pset_values={"AssetTagging": {"SerialNumber": "SN-AHU-001"}},
    )


def test_ifc_space_maps_to_bir_space(bir_mapper):
    """IfcSpace → bir_id kind=space, haystack:space tag, bir:hasIfcGuid (REQ-SOS-028)."""
    turtle = bir_mapper.to_turtle(_good_space(), TENANT_A)
    assert "urn:bir:space:" in turtle
    assert 'bir:customTag "haystack:space"' in turtle
    assert f'bir:hasIfcGuid "{_SPACE_GUID}"' in turtle
    assert "rec:Room" in turtle


def test_ifc_ahu_maps_to_bir_device(bir_mapper):
    """IfcAirHandlingUnit → kind=device, haystack:ahu + haystack:hvac tags."""
    turtle = bir_mapper.to_turtle(_good_ahu(), TENANT_A)
    assert "urn:bir:device:" in turtle
    assert 'bir:customTag "haystack:ahu"' in turtle
    assert 'bir:customTag "haystack:hvac"' in turtle
    assert "brick:Equipment" in turtle


def test_bir_id_is_uuid_v5_from_guid(bir_mapper):
    """Same IFC GUID always produces the same bir_id (deterministic, ADR-006)."""
    turtle1 = bir_mapper.to_turtle(_good_space(), TENANT_A)
    turtle2 = bir_mapper.to_turtle(_good_space(), TENANT_A)
    assert turtle1 == turtle2


def test_pipeline_writes_to_kg_store(kg_store, null_pub):
    """BimLoadPipeline sends one write per entity to KgStorePort (REQ-SOS-028)."""
    pipeline = BimLoadPipeline(
        ifc_parser=MockIfcParser([_good_space(), _good_ahu()]),
        kg_store=kg_store,
        publisher=null_pub,
    )
    result = pipeline.run(b"", TENANT_A)
    assert result.quality_passed is True
    assert result.total_entities == 2
    assert len(kg_store.received_turtles) == 2


def test_nats_completion_event_published(kg_store, null_pub):
    """Successful pipeline run publishes bim-load-completed event (REQ-SOS-032)."""
    pipeline = BimLoadPipeline(
        ifc_parser=MockIfcParser([_good_space()]),
        kg_store=kg_store,
        publisher=null_pub,
    )
    pipeline.run(b"", TENANT_A)
    assert len(null_pub.events) == 1
    assert null_pub.events[0]["type"] == "bim-load-completed"
    assert null_pub.events[0]["total_entities"] == 1
    assert null_pub.events[0]["tenant_id"] == TENANT_A
