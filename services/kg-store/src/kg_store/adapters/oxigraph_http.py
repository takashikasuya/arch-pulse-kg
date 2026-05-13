import httpx

from ..ports.triplestore import TriplestoreRepository


class OxigraphHttpRepository(TriplestoreRepository):
    """Production adapter — talks to Oxigraph HTTP API.

    Env var SPARQL_ENDPOINT selects the Oxigraph base URL so this
    container can be split from Oxigraph later with zero code changes.
    """

    def __init__(self, endpoint: str) -> None:
        self._client = httpx.AsyncClient(
            base_url=endpoint.rstrip("/"), timeout=30.0
        )

    async def sparql_query(
        self, sparql: str, accept: str = "application/sparql-results+json"
    ) -> bytes:
        r = await self._client.post(
            "/query",
            content=sparql.encode(),
            headers={
                "Content-Type": "application/sparql-query",
                "Accept": accept,
            },
        )
        r.raise_for_status()
        return r.content

    async def sparql_update(self, sparql: str) -> None:
        r = await self._client.post(
            "/update",
            content=sparql.encode(),
            headers={"Content-Type": "application/sparql-update"},
        )
        r.raise_for_status()

    async def load_turtle(self, turtle: str, graph_uri: str | None = None) -> None:
        params: dict = {"graph": graph_uri} if graph_uri else {"default": ""}
        r = await self._client.put(
            "/store",
            content=turtle.encode(),
            headers={"Content-Type": "text/turtle"},
            params=params,
        )
        r.raise_for_status()

    async def get_graph_turtle(self, graph_uri: str) -> str:
        r = await self._client.get(
            "/store",
            headers={"Accept": "text/turtle"},
            params={"graph": graph_uri},
        )
        if r.status_code == 404:
            return ""
        r.raise_for_status()
        return r.text

    async def triple_count(self) -> int:
        import json

        raw = await self.sparql_query(
            "SELECT (COUNT(*) AS ?c) WHERE { ?s ?p ?o }",
            accept="application/sparql-results+json",
        )
        data = json.loads(raw)
        bindings = data.get("results", {}).get("bindings", [])
        return int(bindings[0]["c"]["value"]) if bindings else 0

    async def is_alive(self) -> bool:
        try:
            # Oxigraph has no /health; use a trivial ASK query instead
            r = await self._client.get(
                "/query",
                params={"query": "ASK {}"},
                headers={"Accept": "application/sparql-results+json"},
            )
            return r.status_code == 200
        except Exception:
            return False

    async def aclose(self) -> None:
        await self._client.aclose()
