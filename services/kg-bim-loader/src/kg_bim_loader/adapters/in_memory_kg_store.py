"""Test adapter: in-memory KG-Store that records received turtle strings."""
from __future__ import annotations
from ..ports.kg_store import KgStorePort


class InMemoryKgStorePort(KgStorePort):
    def __init__(self) -> None:
        self.received_turtles: list[str] = []

    def write_turtle(self, turtle: str, tenant_id: str) -> None:
        self.received_turtles.append(turtle)
