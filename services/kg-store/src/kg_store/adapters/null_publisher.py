"""No-op event publisher — for tests and offline mode."""
from ..ports.events import ChangeEventPublisher


class NullPublisher(ChangeEventPublisher):
    def __init__(self) -> None:
        self.published: list[dict] = []

    async def publish_bir_updated(
        self,
        tid: str,
        bir_id: str,
        added_triples: list[tuple[str, str, str]],
        removed_triples: list[tuple[str, str, str]],
    ) -> None:
        self.published.append(
            {
                "tid": tid,
                "bir_id": bir_id,
                "added": added_triples,
                "removed": removed_triples,
            }
        )
