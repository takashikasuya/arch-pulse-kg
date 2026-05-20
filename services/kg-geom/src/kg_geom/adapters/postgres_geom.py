"""PostgreSQL/PostGIS repository (production adapter)."""
from __future__ import annotations
import json
from typing import Any
from ..domain.models import GeomRecord
from ..ports.geom_repository import GeomRepository


class PostgresGeomRepository(GeomRepository):
    """Production adapter backed by asyncpg + PostGIS.

    Initialise with an asyncpg connection pool; used in the FastAPI lifespan context.
    """

    def __init__(self, pool: Any) -> None:
        self._pool = pool

    def write(self, record: GeomRecord) -> None:
        raise NotImplementedError("Use async write_async in production context")

    def get(self, uuid: str, tid: str) -> GeomRecord | None:
        raise NotImplementedError("Use async get_async in production context")

    def lookup_space_by_point(self, tid: str, x: float, y: float, z: float) -> str | None:
        raise NotImplementedError("Use async lookup_async in production context")

    def nearby_assets(
        self, tid: str, x: float, y: float, z: float, radius_m: float
    ) -> list[str]:
        raise NotImplementedError("Use async nearby_async in production context")
