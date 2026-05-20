"""Domain models for CS-KG-GEOM."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any


@dataclass
class GeomRecord:
    bir_id: str
    tid: str
    geom_type: str        # polygon | point | line | multipolygon
    geom: dict[str, Any]  # GeoJSON geometry dict
    altitude_m: float = 0.0
    space_bir_id: str | None = None  # for polygon records: the space this geom belongs to
