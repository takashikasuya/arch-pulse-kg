"""In-memory geometry repository using shapely for spatial operations (test adapter)."""
from __future__ import annotations
import re
from shapely.geometry import shape, Point
from ..domain.models import GeomRecord
from ..ports.geom_repository import GeomRepository

_UUID_RE = re.compile(
    r"^urn:bir:[a-z]+:([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})$"
)


def _extract_uuid(bir_id: str) -> str:
    m = _UUID_RE.match(bir_id)
    return m.group(1) if m else bir_id


class MemGeomRepository(GeomRepository):
    def __init__(self) -> None:
        self._store: dict[str, GeomRecord] = {}  # uuid → record

    def write(self, record: GeomRecord) -> None:
        key = _extract_uuid(record.bir_id)
        self._store[key] = record

    def get(self, uuid: str) -> GeomRecord | None:
        return self._store.get(uuid)

    def lookup_space_by_point(self, tid: str, x: float, y: float, z: float) -> str | None:
        pt = Point(x, y)
        for rec in self._store.values():
            if rec.tid != tid or rec.geom_type != "polygon":
                continue
            poly = shape(rec.geom)
            if poly.contains(pt):
                return rec.space_bir_id or rec.bir_id
        return None

    def nearby_assets(
        self, tid: str, x: float, y: float, z: float, radius_m: float
    ) -> list[str]:
        pt = Point(x, y)
        results = []
        for rec in self._store.values():
            if rec.tid != tid:
                continue
            try:
                centroid = shape(rec.geom).centroid
                if pt.distance(centroid) <= radius_m:
                    results.append(rec.bir_id)
            except Exception:
                pass
        return results
