"""Health endpoint."""
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

router = APIRouter()


@router.get("/healthz")
async def healthz(request: Request) -> JSONResponse:
    kg: object = request.app.state.kg
    alive = await kg.is_alive()
    return JSONResponse({"status": "ok" if alive else "degraded", "kg_alive": alive})
