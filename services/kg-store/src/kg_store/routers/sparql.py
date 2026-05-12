"""SPARQL 1.1 / SPARQL-star proxy (IF-KG-001)."""
from fastapi import APIRouter, Request, Response, Body, Header, HTTPException
from fastapi.responses import Response as FastResponse

router = APIRouter()

_DEFAULT_ACCEPT = "application/sparql-results+json"


@router.get("/sparql")
async def sparql_get(request: Request, query: str) -> FastResponse:
    accept = request.headers.get("accept", _DEFAULT_ACCEPT)
    repo = request.app.state.repo
    raw = await repo.sparql_query(query, accept)
    content_type = accept.split(",")[0].strip()
    return FastResponse(content=raw, media_type=content_type)


@router.post("/sparql")
async def sparql_post(request: Request) -> FastResponse:
    content_type = request.headers.get("content-type", "")
    accept = request.headers.get("accept", _DEFAULT_ACCEPT)
    repo = request.app.state.repo

    if "application/sparql-query" in content_type:
        body = await request.body()
        sparql = body.decode()
    elif "application/x-www-form-urlencoded" in content_type:
        form = await request.form()
        sparql = form.get("query", "")
        if not sparql:
            raise HTTPException(400, "Missing 'query' parameter")
    else:
        raise HTTPException(415, "Unsupported Content-Type for SPARQL query")

    raw = await repo.sparql_query(sparql, accept)
    ct = accept.split(",")[0].strip()
    return FastResponse(content=raw, media_type=ct)


@router.post("/sparql-update", status_code=204)
async def sparql_update(request: Request) -> None:
    content_type = request.headers.get("content-type", "")
    repo = request.app.state.repo

    if "application/sparql-update" in content_type:
        body = await request.body()
        update = body.decode()
    elif "application/x-www-form-urlencoded" in content_type:
        form = await request.form()
        update = form.get("update", "")
        if not update:
            raise HTTPException(400, "Missing 'update' parameter")
    else:
        raise HTTPException(415, "Unsupported Content-Type for SPARQL update")

    await repo.sparql_update(update)
