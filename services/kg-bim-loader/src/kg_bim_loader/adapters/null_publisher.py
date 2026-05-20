"""Test adapter: null publisher that records published events."""
from __future__ import annotations
from ..ports.events import ChangeEventPublisher


class NullPublisher(ChangeEventPublisher):
    def __init__(self) -> None:
        self.events: list[dict] = []

    def publish(self, subject: str, payload: dict) -> None:
        self.events.append({"subject": subject, **payload})
