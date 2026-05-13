"""TimescaleDB reader port — IF-INFRA-002."""
from abc import ABC, abstractmethod


class TsReader(ABC):
    @abstractmethod
    async def query_telemetry(
        self,
        tenant_id: str,
        bir_point_id: str,
        start: str,
        end: str,
        bucket: str = "PT1H",
    ) -> list[dict]:
        """Return aggregated telemetry rows for a bir:point entity."""
