"""Causal analysis endpoint — FUN-ENERGY-002 / FUN-ENERGY-003."""
import re
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse

from ..domain.models import AnalysisRequest
from ..services.causal_analysis import run_causal_analysis

router = APIRouter(prefix="/analysis")

_BIR_ID_RE = re.compile(
    r"^urn:bir:[a-z][a-z\-]*:[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
)


@router.post("/causal")
async def causal_analysis(body: AnalysisRequest, request: Request) -> JSONResponse:
    """Run GraphRAG causal analysis against KG-STORE and return citation-annotated paths."""
    if not _BIR_ID_RE.match(body.context_bir_id):
        raise HTTPException(422, f"Invalid context_bir_id format: {body.context_bir_id!r}")

    kg = request.app.state.kg
    ts = request.app.state.ts

    result = await run_causal_analysis(body, kg, ts)
    return JSONResponse(result.model_dump())
