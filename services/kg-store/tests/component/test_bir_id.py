"""Unit tests for the bir_id domain module (pure Python, no network)."""
import pytest
import uuid

from kg_store.domain import bir_id as mod


def test_parse_valid_space():
    b = mod.parse("urn:bir:space:550e8400-e29b-41d4-a716-446655440000")
    assert b.kind == "space"
    assert str(b.uid) == "550e8400-e29b-41d4-a716-446655440000"
    assert b.raw == "urn:bir:space:550e8400-e29b-41d4-a716-446655440000"


def test_parse_valid_ctrl_seq():
    raw = "urn:bir:ctrl-seq:f47ac10b-58cc-4372-a567-0e02b2c3d479"
    b = mod.parse(raw)
    assert b.kind == "ctrl-seq"


def test_parse_invalid_format_raises():
    with pytest.raises(ValueError, match="Invalid bir_id format"):
        mod.parse("not-a-bir-id")


def test_parse_unknown_kind_raises():
    # lowercase but not in BIR_KINDS → "Unknown bir_id kind"
    with pytest.raises(ValueError, match="Unknown bir_id kind"):
        mod.parse("urn:bir:notakind:550e8400-e29b-41d4-a716-446655440000")


def test_parse_uppercase_uuid_raises():
    with pytest.raises(ValueError, match="Invalid bir_id format"):
        mod.parse("urn:bir:space:550E8400-E29B-41D4-A716-446655440000")


def test_from_ifc_guid_is_deterministic():
    b1 = mod.from_ifc_guid("space", "3mXkZ9JyP9YgmW4eS_xxxx")
    b2 = mod.from_ifc_guid("space", "3mXkZ9JyP9YgmW4eS_xxxx")
    assert b1 == b2


def test_from_ifc_guid_different_inputs_differ():
    b1 = mod.from_ifc_guid("space", "IFC_GUID_A")
    b2 = mod.from_ifc_guid("space", "IFC_GUID_B")
    assert b1.uid != b2.uid


def test_from_ifc_guid_result_is_parseable():
    b = mod.from_ifc_guid("device", "SomeIfcGuid123")
    mod.parse(b.raw)  # must not raise


def test_new_generates_valid_bir_id():
    b = mod.new("building")
    mod.parse(b.raw)  # must not raise
    assert b.kind == "building"


def test_to_nats_slug():
    slug = mod.to_nats_slug("urn:bir:space:550e8400-e29b-41d4-a716-446655440000")
    assert ":" not in slug
    assert slug.startswith("urn-bir-space-")


def test_all_known_kinds_parseable():
    for kind in mod.BIR_KINDS:
        raw = f"urn:bir:{kind}:550e8400-e29b-41d4-a716-446655440000"
        b = mod.parse(raw)
        assert b.kind == kind
