"""KG reader port — IF-KG-001 (SPARQL 1.1)."""
from abc import ABC, abstractmethod


class KgReader(ABC):
    @abstractmethod
    async def sparql_select(self, query: str) -> list[dict[str, dict]]:
        """Execute a SPARQL SELECT and return bindings list."""

    @abstractmethod
    async def is_alive(self) -> bool: ...
