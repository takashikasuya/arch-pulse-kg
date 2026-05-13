"""In-memory triplestore adapter using pyoxigraph — for tests only."""
import io
import json
from typing import Any

import pyoxigraph as ox

from ..ports.triplestore import TriplestoreRepository


def _term_to_sparql_json(term: Any) -> dict:
    if isinstance(term, ox.NamedNode):
        return {"type": "uri", "value": term.value}
    if isinstance(term, ox.BlankNode):
        return {"type": "bnode", "value": term.value}
    if isinstance(term, ox.Literal):
        result: dict = {"type": "literal", "value": term.value}
        if term.language:
            result["xml:lang"] = term.language
        elif term.datatype and term.datatype.value != "http://www.w3.org/2001/XMLSchema#string":
            result["datatype"] = term.datatype.value
        return result
    raise TypeError(f"Unknown RDF term: {type(term)}")


class PyoxigraphMemRepository(TriplestoreRepository):
    def __init__(self) -> None:
        self._store = ox.Store()

    async def sparql_query(
        self, sparql: str, accept: str = "application/sparql-results+json"
    ) -> bytes:
        result = self._store.query(sparql)
        if isinstance(result, bool):
            return json.dumps({"boolean": result}).encode()
        if hasattr(result, "variables"):
            variables = [v.value for v in result.variables]
            bindings = []
            for solution in result:
                row = {}
                for var in result.variables:
                    val = solution[var]
                    if val is not None:
                        row[var.value] = _term_to_sparql_json(val)
                bindings.append(row)
            return json.dumps(
                {"head": {"vars": variables}, "results": {"bindings": bindings}}
            ).encode()
        # CONSTRUCT / DESCRIBE → serialize triples as Turtle
        buf = io.BytesIO()
        triples = list(result)
        for triple in triples:
            subj = f"<{triple.subject.value}>"
            pred = f"<{triple.predicate.value}>"
            obj_term = triple.object
            if isinstance(obj_term, ox.NamedNode):
                obj = f"<{obj_term.value}>"
            elif isinstance(obj_term, ox.BlankNode):
                obj = f"_:{obj_term.value}"
            elif isinstance(obj_term, ox.Literal):
                escaped = obj_term.value.replace("\\", "\\\\").replace('"', '\\"')
                if obj_term.language:
                    obj = f'"{escaped}"@{obj_term.language}'
                else:
                    obj = f'"{escaped}"^^<{obj_term.datatype.value}>'
            else:
                obj = str(obj_term)
            buf.write(f"{subj} {pred} {obj} .\n".encode())
        return buf.getvalue()

    async def sparql_update(self, sparql: str) -> None:
        self._store.update(sparql)

    async def load_turtle(self, turtle: str, graph_uri: str | None = None) -> None:
        data = io.BytesIO(turtle.encode())
        if graph_uri:
            self._store.load(data, mime_type="text/turtle", to_graph=ox.NamedNode(graph_uri))
        else:
            self._store.load(data, mime_type="text/turtle")

    async def get_graph_turtle(self, graph_uri: str) -> str:
        buf = io.BytesIO()
        try:
            self._store.dump(buf, mime_type="text/turtle", from_graph=ox.NamedNode(graph_uri))
            return buf.getvalue().decode()
        except Exception:
            return ""

    async def triple_count(self) -> int:
        result = self._store.query("SELECT (COUNT(*) AS ?c) WHERE { ?s ?p ?o }")
        for solution in result:
            val = solution["c"]
            return int(val.value) if val else 0
        return 0

    async def is_alive(self) -> bool:
        return True
