"""TimescaleDB HTTP adapter — consumes IF-INFRA-002."""
from __future__ import annotations
import urllib.parse
import httpx
from ..ports.ts_reader import TsReader


class TimescaleHttpClient(TsReader):
    def __init__(self, base_url: str) -> None:
        self._client = httpx.AsyncClient(base_url=base_url, timeout=30.0)

    async def query_telemetry(
        self,
        tenant_id: str,
        bir_point_id: str,
        start: str,
        end: str,
        bucket: str = "PT1H",
    ) -> list[dict]:
        tid_enc = urllib.parse.quote(tenant_id, safe="")
        point_kind = "energy"  # derived from bir_point_id in future versions
        r = await self._client.get(
            f"/tenants/{tid_enc}/telemetry/{point_kind}",
            params={"from": start, "to": end, "bucket": bucket, "bir_id": bir_point_id},
        )
        r.raise_for_status()
        return r.json().get("rows", [])

    async def aclose(self) -> None:
        await self._client.aclose()
