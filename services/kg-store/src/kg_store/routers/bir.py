"""BIR entity write/read and external-ID lookup (REQ-SOS-028)."""
import json
import re
from fastapi import APIRouter, Request, HTTPException, Response
from fastapi.responses import JSONResponse

from ..domain import bir_id as bir_id_mod
from ..domain.models import BirLookupResult, BeaconLookupResult, ExternalRefs

router = APIRouter(prefix="/bir")

BIR_NS = "https://arch-pulse.example/ns/bir#"

# Must stay in sync with sh:pattern in bir:BeaconShape (bir_shapes.ttl)
_BEACON_ID_RE = re.compile(r"^urn:beacon:[A-Za-z0-9][A-Za-z0-9\-_:.]*$")

# Map query param 'system' value → RDF predicate
_SYSTEM_PREDICATE: dict[str, str] = {
    "ifc":        f"{BIR_NS}hasIfcGuid",
    "revit":      f"{BIR_NS}hasRevitElementId",
    "gbxml":      f"{BIR_NS}hasGbxmlSpaceId",
    "energyplus": f"{BIR_NS}hasEnergyPlusZone",
    "p223":       f"{BIR_NS}hasP223SpaceUri",
    "bas":        f"{BIR_NS}hasBasPointPrefix",
    "brick":      f"{BIR_NS}hasBrickUri",
}


@router.post("/entities", status_code=201)
async def write_entity(request: Request) -> JSONResponse:
    """Accept RDF/Turtle for a bir:Entity, validate with SHACL, write to store."""
    body_bytes = await request.body()
    turtle = body_bytes.decode()

    shapes_ttl: str = request.app.state.bir_shapes_ttl
    conforms, report_graph, _ = _run_shacl(turtle, shapes_ttl)
    if not conforms:
        import io
        buf = io.BytesIO()
        report_graph.serialize(buf, format="turtle")
        raise HTTPException(
            422,
            detail={
                "error": "SHACL validation failed",
                "report": buf.getvalue().decode(),
            },
        )

    repo = request.app.state.repo
    publisher = request.app.state.publisher

    bir_id = _extract_bir_id(turtle)
    if not bir_id:
        raise HTTPException(400, "No bir:Entity subject (urn:bir:*) found in provided Turtle")
    before = await _get_entity_triples(repo, bir_id)

    # Atomic replace: delete all existing triples for this entity, then insert new ones.
    delete_sparql = f"DELETE WHERE {{ <{bir_id}> ?p ?o }}"
    insert_sparql = _turtle_to_insert(turtle)
    await repo.sparql_update(delete_sparql)
    await repo.sparql_update(insert_sparql)

    after = await _get_entity_triples(repo, bir_id)
    added = list(after - before)
    removed = list(before - after)

    default_tid = "urn:bir:tenant:00000000-0000-0000-0000-000000000000"
    try:
        await publisher.publish_bir_updated(default_tid, bir_id, added, removed)
    except Exception:
        import logging
        logging.getLogger(__name__).warning("NATS publish failed for %s; write committed", bir_id)

    return JSONResponse({"bir_id": bir_id, "status": "written"}, status_code=201)


@router.get("/entities/{bir_id:path}")
async def get_entity(bir_id: str, request: Request) -> Response:
    """Return all triples for a given bir_id as Turtle."""
    repo = request.app.state.repo
    try:
        bir_id_mod.parse(bir_id)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc

    sparql = f"""
    CONSTRUCT {{ <{bir_id}> ?p ?o }}
    WHERE     {{ <{bir_id}> ?p ?o }}
    """
    raw = await repo.sparql_query(sparql, accept="text/turtle")
    if not raw.strip():
        raise HTTPException(404, f"Entity not found: {bir_id}")
    return Response(content=raw, media_type="text/turtle")


@router.get("/lookup")
async def lookup(system: str, id: str, request: Request) -> JSONResponse:
    """Lookup bir_id by external system identifier (REQ-SOS-028 bidirectional)."""
    pred = _SYSTEM_PREDICATE.get(system)
    if not pred:
        raise HTTPException(400, f"Unknown system: {system!r}. Choose from: {list(_SYSTEM_PREDICATE)}")

    repo = request.app.state.repo
    import rdflib
    id_literal = rdflib.Literal(id).n3()
    sparql = f"""
    PREFIX bir: <{BIR_NS}>
    SELECT ?entity ?status WHERE {{
        ?entity a bir:Entity ;
                <{pred}> {id_literal} ;
                bir:status ?status .
    }}
    LIMIT 1
    """
    raw = await repo.sparql_query(sparql, accept="application/sparql-results+json")
    data = json.loads(raw)
    bindings = data.get("results", {}).get("bindings", [])
    if not bindings:
        raise HTTPException(404, f"No bir_id found for {system}={id!r}")

    row = bindings[0]
    found_bir_id = row["entity"]["value"]
    status = row["status"]["value"]
    parsed = bir_id_mod.parse(found_bir_id)

    return JSONResponse(
        BirLookupResult(
            bir_id=found_bir_id,
            kind=parsed.kind,
            status=status,
            external_refs=ExternalRefs(**{_predicate_to_field(pred): id}),
        ).model_dump()
    )


# ── Beacon endpoints (Issue #1, Slice 6-a) ────────────────────────────────────

@router.post("/beacons", status_code=201)
async def write_beacon(request: Request) -> JSONResponse:
    """Register a bir:Beacon entity (urn:beacon:{id}) linked to a space bir_id."""
    body_bytes = await request.body()
    turtle = body_bytes.decode()

    shapes_ttl: str = request.app.state.bir_shapes_ttl
    conforms, report_graph, _ = _run_shacl(turtle, shapes_ttl)
    if not conforms:
        import io
        buf = io.BytesIO()
        report_graph.serialize(buf, format="turtle")
        raise HTTPException(422, detail={"error": "SHACL validation failed",
                                         "report": buf.getvalue().decode()})

    beacon_id = _extract_beacon_id(turtle)
    if not beacon_id:
        raise HTTPException(400, "No bir:Beacon subject (urn:beacon:*) found in provided Turtle")

    repo = request.app.state.repo
    delete_sparql = f"DELETE WHERE {{ <{beacon_id}> ?p ?o }}"
    insert_sparql = _turtle_to_insert(turtle)
    await repo.sparql_update(delete_sparql)
    await repo.sparql_update(insert_sparql)

    return JSONResponse({"beacon_id": beacon_id, "status": "written"}, status_code=201)


@router.get("/beacon-lookup")
async def beacon_lookup(beacon_id: str, request: Request) -> JSONResponse:
    """Resolve a beacon ID to the space bir_id it is located in."""
    if not _BEACON_ID_RE.match(beacon_id):
        raise HTTPException(400, f"Invalid beacon_id format: {beacon_id!r}. "
                                 "Expected urn:beacon:{{hardware-id}}")

    repo = request.app.state.repo
    sparql = f"""
    PREFIX bir: <{BIR_NS}>
    SELECT ?bir_id WHERE {{
        <{beacon_id}> bir:locatedIn ?bir_id .
    }}
    LIMIT 1
    """
    raw = await repo.sparql_query(sparql, accept="application/sparql-results+json")
    data = json.loads(raw)
    bindings = data.get("results", {}).get("bindings", [])
    if not bindings:
        raise HTTPException(404, f"No space found for beacon {beacon_id!r}")

    found_bir_id = bindings[0]["bir_id"]["value"]
    try:
        parsed = bir_id_mod.parse(found_bir_id)
    except ValueError as exc:
        raise HTTPException(500, f"Stored bir_id is invalid: {found_bir_id!r}") from exc

    return JSONResponse(
        BeaconLookupResult(beacon_id=beacon_id, bir_id=found_bir_id, kind=parsed.kind).model_dump()
    )


# ── helpers ──────────────────────────────────────────────────────────────────

def _run_shacl(data_ttl: str, shapes_ttl: str):
    from pyshacl import validate  # type: ignore[import]

    return validate(
        data_graph=data_ttl,
        shacl_graph=shapes_ttl,
        data_graph_format="turtle",
        shacl_graph_format="turtle",
        inference="none",
    )


def _extract_bir_id(turtle: str) -> str:
    """Extract the first IRI subject from Turtle — simple heuristic for v0.1."""
    import rdflib

    g = rdflib.Graph()
    g.parse(data=turtle, format="turtle")
    for s in g.subjects():
        if isinstance(s, rdflib.URIRef) and str(s).startswith("urn:bir:"):
            return str(s)
    return ""


def _extract_beacon_id(turtle: str) -> str:
    """Extract the first urn:beacon: subject from Turtle."""
    import rdflib

    g = rdflib.Graph()
    g.parse(data=turtle, format="turtle")
    for s in g.subjects():
        if isinstance(s, rdflib.URIRef) and str(s).startswith("urn:beacon:"):
            return str(s)
    return ""


def _turtle_to_insert(turtle: str) -> str:
    """Convert Turtle data to a SPARQL INSERT DATA statement via N-Triples.

    Turtle's @prefix declarations are not valid inside SPARQL INSERT DATA;
    converting to N-Triples avoids that pitfall.
    """
    import rdflib

    g = rdflib.Graph()
    g.parse(data=turtle, format="turtle")
    triples = "".join(f"  {s.n3()} {p.n3()} {o.n3()} .\n" for s, p, o in g)
    return f"INSERT DATA {{\n{triples}}}"


async def _get_entity_triples(repo, bir_id: str) -> set[tuple[str, str, str]]:
    """Fetch all (bir_id, p, o) as string tuples for diff computation."""
    sparql = f"SELECT ?p ?o WHERE {{ <{bir_id}> ?p ?o }}"
    raw = await repo.sparql_query(sparql, accept="application/sparql-results+json")
    data = json.loads(raw)
    triples: set[tuple[str, str, str]] = set()
    for b in data.get("results", {}).get("bindings", []):
        p = b["p"]["value"]
        o_node = b["o"]
        if o_node["type"] == "uri":
            o = o_node["value"]
        else:
            o = o_node.get("value", "")
        triples.add((bir_id, p, o))
    return triples


def _predicate_to_field(pred: str) -> str:
    suffix = pred.split("#")[-1]
    mapping = {
        "hasIfcGuid":        "ifc_guid",
        "hasRevitElementId": "revit_element_id",
        "hasGbxmlSpaceId":   "gbxml_space_id",
        "hasEnergyPlusZone": "energyplus_zone",
        "hasP223SpaceUri":   "p223_space_uri",
        "hasBasPointPrefix": "bas_point_prefix",
        "hasBrickUri":       "brick_uri",
    }
    return mapping.get(suffix, suffix)
