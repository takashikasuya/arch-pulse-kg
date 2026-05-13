from abc import ABC, abstractmethod


class TriplestoreRepository(ABC):
    @abstractmethod
    async def sparql_query(
        self, sparql: str, accept: str = "application/sparql-results+json"
    ) -> bytes: ...

    @abstractmethod
    async def sparql_update(self, sparql: str) -> None: ...

    @abstractmethod
    async def load_turtle(self, turtle: str, graph_uri: str | None = None) -> None: ...

    @abstractmethod
    async def get_graph_turtle(self, graph_uri: str) -> str: ...

    @abstractmethod
    async def triple_count(self) -> int: ...

    @abstractmethod
    async def is_alive(self) -> bool: ...

    async def aclose(self) -> None:
        pass
