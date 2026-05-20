"""Port: geometry repository abstraction."""
from __future__ import annotations
from abc import ABC, abstractmethod
from ..domain.models import GeomRecord


class GeomRepository(ABC):
    @abstractmethod
    def write(self, record: GeomRecord) -> None: ...

    @abstractmethod
    def get(self, uuid: str, tid: str) -> GeomRecord | None: ...

    @abstractmethod
    def lookup_space_by_point(self, tid: str, x: float, y: float, z: float) -> str | None:
        """Return bir_id of the space polygon that contains point (x, y) at given altitude."""
        ...

    @abstractmethod
    def nearby_assets(
        self, tid: str, x: float, y: float, z: float, radius_m: float
    ) -> list[str]:
        """Return bir_ids of all records within radius_m of point (x, y) for tenant tid."""
        ...
