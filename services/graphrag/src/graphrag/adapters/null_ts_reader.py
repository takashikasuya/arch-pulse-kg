"""Null TimescaleDB reader — returns empty rows (used when TS_DB_URL is unset)."""
from ..ports.ts_reader import TsReader


class NullTsReader(TsReader):
    async def query_telemetry(self, tenant_id, bir_point_id, start, end, bucket="PT1H"):
        return []
