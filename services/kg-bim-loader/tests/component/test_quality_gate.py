"""Component tests for IFC quality gate (#10, REQ-SOS-026)."""
import json
import pytest
from pathlib import Path

from kg_bim_loader.domain.ifc_model import IfcEntity, Face
from kg_bim_loader.adapters.mock_ifc_parser import MockIfcParser


def _good_entity(guid: str = "GOOD0000001") -> IfcEntity:
    return IfcEntity(
        ifc_guid=guid,
        ifc_class="IfcSpace",
        name="Test Room",
        faces=[
            Face(area=5.0, normal=(0.0, 0.0, 1.0)),
            Face(area=3.0, normal=(1.0, 0.0, 0.0)),
        ],
        boundary_gaps=0.0,
    )


def test_good_ifc_passes(quality_gate):
    """Well-formed entities pass all quality checks (REQ-SOS-026)."""
    result = quality_gate.run([_good_entity()])
    assert result.passed is True
    assert result.violations == []


def test_sliver_face_rejected(quality_gate):
    """Face with area < 0.001 m² triggers sliver violation."""
    entity = IfcEntity(
        ifc_guid="SLIVER001",
        ifc_class="IfcSpace",
        faces=[Face(area=0.0001, normal=(0.0, 0.0, 1.0))],
    )
    result = quality_gate.run([entity])
    assert result.passed is False
    assert any(v.violation_type == "sliver" for v in result.violations)


def test_reversed_normals_rejected(quality_gate):
    """Face with normal pointing straight down triggers reversed_normals violation."""
    entity = IfcEntity(
        ifc_guid="REVNORM01",
        ifc_class="IfcSpace",
        faces=[Face(area=5.0, normal=(0.0, 0.0, -1.0))],
    )
    result = quality_gate.run([entity])
    assert result.passed is False
    assert any(v.violation_type == "reversed_normals" for v in result.violations)


def test_gap_detected(quality_gate):
    """Boundary gap > 5 mm triggers gap violation."""
    entity = IfcEntity(
        ifc_guid="GAP00001",
        ifc_class="IfcSpace",
        boundary_gaps=10.0,
    )
    result = quality_gate.run([entity])
    assert result.passed is False
    assert any(v.violation_type == "gap" for v in result.violations)


def test_missing_guid_rejected(quality_gate):
    """Empty ifc_guid triggers missing_required_attr violation."""
    entity = IfcEntity(ifc_guid="", ifc_class="IfcSpace")
    result = quality_gate.run([entity])
    assert result.passed is False
    assert any(v.violation_type == "missing_required_attr" for v in result.violations)


def test_report_json_written(quality_gate, tmp_path):
    """Quality gate failure produces a valid JSON report with violations."""
    entity = IfcEntity(
        ifc_guid="SLIVER002",
        ifc_class="IfcSpace",
        faces=[Face(area=0.0005, normal=(0.0, 0.0, 1.0))],
    )
    result = quality_gate.run([entity])
    assert result.passed is False

    report_path = tmp_path / "report.json"
    result.write_report(report_path)

    data = json.loads(report_path.read_text())
    assert data["passed"] is False
    assert len(data["violations"]) >= 1
    assert data["violations"][0]["violation_type"] == "sliver"
