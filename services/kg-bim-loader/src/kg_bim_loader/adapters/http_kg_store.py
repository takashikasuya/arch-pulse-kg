"""Production adapter: writes BIR Turtle to CS-KG-STORE via POST /bir/entities."""
from __future__ import annotations
import httpx
from ..ports.kg_store import KgStorePort


class HttpKgStorePort(KgStorePort):
    def __init__(self, base_url: str) -> None:
        self._base_url = base_url.rstrip("/")

    def write_turtle(self, turtle: str, tenant_id: str) -> None:
        r = httpx.post(
            f"{self._base_url}/bir/entities",
            content=turtle.encode(),
            headers={"Content-Type": "text/turtle"},
            timeout=30.0,
        )
        r.raise_for_status()
