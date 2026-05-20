"""IF-KG-002 geometry endpoints + spatial query endpoints."""
from __future__ import annotations
import hashlib
import json
import re
from typing import Any

from fastapi import APIRouter, HTTPException, Query, Request, Response
from pydantic import BaseModel
from typing import Literal

router = APIRouter(prefix="/geom")

_TENANT_RE = re.compile(
    r"^urn:bir:tenant:[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
)
_UUID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
)


def _validate_tenant(tid: str) -> None:
    if not _TENANT_RE.match(tid):
        raise HTTPException(422, detail=f"Invalid tenant_id format: {tid}")


def _etag(bir_id: str, geom: dict) -> str:
    content = f"{bir_id}:{json.dumps(geom, sort_keys=True)}"
    digest = hashlib.sha256(content.encode()).hexdigest()[:16]
    return f'"{digest}"'


class WriteGeomRequest(BaseModel):
    bir_id: str
    tid: str
    geom_type: Literal["point", "polygon"]
    geom: dict[str, Any]
    altitude_m: float = 0.0
    space_bir_id: str | None = None


@router.post("/write", status_code=201)
def write_geometry(body: WriteGeomRequest, request: Request):
    _validate_tenant(body.tid)
    from ..domain.models import GeomRecord

    repo = request.app.state.repo
    record = GeomRecord(
        bir_id=body.bir_id,
        tid=body.tid,
        geom_type=body.geom_type,
        geom=body.geom,
        altitude_m=body.altitude_m,
        space_bir_id=body.space_bir_id,
    )
    repo.write(record)
    return {"bir_id": body.bir_id}


@router.get("/{uuid}")
def get_geometry(
    uuid: str,
    request: Request,
    response: Response,
    tid: str = Query(...),
    lod: str | None = None,  # reserved: LOD rendering not yet implemented
):
    _validate_tenant(tid)
    if not _UUID_RE.match(uuid):
        raise HTTPException(422, detail="Invalid UUID format")
    repo = request.app.state.repo
    record = repo.get(uuid, tid)
    if record is None:
        raise HTTPException(404, detail="Geometry not found")
    tag = _etag(record.bir_id, record.geom)
    response.headers["ETag"] = tag
    return record.geom


@router.head("/{uuid}")
def head_geometry(uuid: str, request: Request, response: Response, tid: str = Query(...)):
    _validate_tenant(tid)
    if not _UUID_RE.match(uuid):
        raise HTTPException(422, detail="Invalid UUID format")
    repo = request.app.state.repo
    record = repo.get(uuid, tid)
    if record is None:
        raise HTTPException(404, detail="Geometry not found")
    response.headers["ETag"] = _etag(record.bir_id, record.geom)
    return Response(headers=response.headers)


@router.get("/lookup/space")
def lookup_space_by_point(
    request: Request,
    tid: str = Query(...),
    x: float = Query(...),
    y: float = Query(...),
    z: float = Query(0.0),
):
    _validate_tenant(tid)
    repo = request.app.state.repo
    bir_id = repo.lookup_space_by_point(tid, x, y, z)
    if bir_id is None:
        raise HTTPException(404, detail="No space found at the given point")
    return {"bir_id": bir_id}


@router.get("/lookup/nearby")
def nearby_assets(
    request: Request,
    tid: str = Query(...),
    x: float = Query(...),
    y: float = Query(...),
    z: float = Query(0.0),
    radius_m: float = Query(...),
):
    _validate_tenant(tid)
    repo = request.app.state.repo
    bir_ids = repo.nearby_assets(tid, x, y, z, radius_m)
    return {"assets": [{"bir_id": b} for b in bir_ids], "count": len(bir_ids)}
