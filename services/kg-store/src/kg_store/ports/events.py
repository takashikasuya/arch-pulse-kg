from abc import ABC, abstractmethod


class ChangeEventPublisher(ABC):
    @abstractmethod
    async def publish_bir_updated(
        self,
        tid: str,
        bir_id: str,
        added_triples: list[tuple[str, str, str]],
        removed_triples: list[tuple[str, str, str]],
    ) -> None: ...

    async def aclose(self) -> None:
        pass
