"""Port: event publisher abstraction."""
from __future__ import annotations
from abc import ABC, abstractmethod


class ChangeEventPublisher(ABC):
    @abstractmethod
    def publish(self, subject: str, payload: dict) -> None: ...
