"""IF-KG-TAGSEARCH — customTags tag search endpoint (REQ-SOS-060, REQ-SOS-061).

GET /tags/search
  ?tags=haystack:hvac&tags=bldg:dr-level-1
  &tenant_id=urn:bir:tenant:00000000-0000-0000-0000-000000000001
  &limit=100
"""
import json
import re

import rdflib
from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import JSONResponse

from ..domain import bir_id as bir_id_mod

router = APIRouter(prefix="/tags")

BIR_NS = "https://arch-pulse.example/ns/bir#"
_TAG_RE = re.compile(r"^(haystack:|bldg:)[A-Za-z0-9][A-Za-z0-9\-_]*$")
_TENANT_RE = re.compile(
    r"^urn:bir:tenant:[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
)
_DEFAULT_LIMIT = 100


@router.get("/search")
async def tag_search(
    request: Request,
    tags: list[str] = Query(..., min_length=1),
    tenant_id: str = Query(...),
    limit: int = Query(default=_DEFAULT_LIMIT, ge=1, le=1000),
) -> JSONResponse:
    if not tags:
        raise HTTPException(400, "At least one tag is required")

    # Validate tag format
    bad_tags = [t for t in tags if not _TAG_RE.match(t)]
    if bad_tags:
        raise HTTPException(422, {"error": "Invalid tag format", "invalid_tags": bad_tags})

    # Validate tenant_id
    if not _TENANT_RE.match(tenant_id):
        raise HTTPException(422, f"Invalid tenant_id format: {tenant_id!r}")

    repo = request.app.state.repo
    sparql = _build_query(tags, tenant_id, limit)
    raw = await repo.sparql_query(sparql, accept="application/sparql-results+json")
    data = json.loads(raw)

    results = _parse_results(data, tags)
    return JSONResponse({"results": results, "count": len(results)})


def _build_query(tags: list[str], tenant_id: str, limit: int) -> str:
    tag_patterns = "\n    ".join(
        f"?entity <{BIR_NS}customTag> {rdflib.Literal(t).n3()} ."
        for t in tags
    )
    return f"""PREFIX bir: <{BIR_NS}>
SELECT DISTINCT ?entity ?ctrl_tmpl WHERE {{
    ?entity a bir:Entity ;
            bir:tenantScope <{tenant_id}> .
    {tag_patterns}
    OPTIONAL {{ ?entity bir:hasControlTemplate ?ctrl_tmpl }}
}}
LIMIT {limit}"""


def _parse_results(data: dict, requested_tags: list[str]) -> list[dict]:
    results = []
    for b in data.get("results", {}).get("bindings", []):
        bir_id_str = b["entity"]["value"]
        try:
            parsed = bir_id_mod.parse(bir_id_str)
        except ValueError:
            continue
        item: dict = {
            "bir_id": bir_id_str,
            "kind": parsed.kind,
            "matched_tags": requested_tags,
        }
        if "ctrl_tmpl" in b:
            item["control_template_id"] = b["ctrl_tmpl"]["value"]
        results.append(item)
    return results
