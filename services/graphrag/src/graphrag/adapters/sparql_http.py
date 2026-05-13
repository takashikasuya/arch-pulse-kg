"""SPARQL HTTP adapter — consumes IF-KG-001 via CS-KG-STORE."""
from __future__ import annotations
import json
import httpx
from ..ports.kg_reader import KgReader


class SparqlHttpClient(KgReader):
    def __init__(self, base_url: str) -> None:
        self._client = httpx.AsyncClient(base_url=base_url, timeout=30.0)

    async def sparql_select(self, query: str) -> list[dict[str, dict]]:
        r = await self._client.post(
            "/sparql",
            content=query,
            headers={
                "Content-Type": "application/sparql-query",
                "Accept": "application/sparql-results+json",
            },
        )
        r.raise_for_status()
        data = json.loads(r.text)
        return data.get("results", {}).get("bindings", [])

    async def is_alive(self) -> bool:
        try:
            r = await self._client.get("/healthz")
            return r.status_code == 200
        except Exception:
            return False

    async def aclose(self) -> None:
        await self._client.aclose()
