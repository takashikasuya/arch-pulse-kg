"""Port: KG-Store write abstraction."""
from __future__ import annotations
from abc import ABC, abstractmethod


class KgStorePort(ABC):
    @abstractmethod
    def write_turtle(self, turtle: str, tenant_id: str) -> None: ...
