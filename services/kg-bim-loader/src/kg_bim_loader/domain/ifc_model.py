"""IFC domain model — abstract representation of parsed IFC entities."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class Face:
    area: float
    normal: tuple[float, float, float]


@dataclass
class IfcEntity:
    ifc_guid: str
    ifc_class: str
    name: str = ""
    faces: list[Face] = field(default_factory=list)
    boundary_gaps: float = 0.0
    pset_values: dict[str, dict[str, str]] = field(default_factory=dict)
