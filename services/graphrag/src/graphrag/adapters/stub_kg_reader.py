"""Stub KG reader for component tests — returns pre-configured SPARQL bindings."""
from __future__ import annotations
from ..ports.kg_reader import KgReader


class StubKgReader(KgReader):
    def __init__(self, bindings: list[dict[str, dict]] | None = None) -> None:
        self._bindings: list[dict[str, dict]] = bindings or []

    def set_bindings(self, bindings: list[dict[str, dict]]) -> None:
        self._bindings = bindings

    async def sparql_select(self, query: str) -> list[dict[str, dict]]:
        return self._bindings

    async def is_alive(self) -> bool:
        return True
