from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

router = APIRouter()


@router.get("/healthz")
async def healthz(request: Request) -> JSONResponse:
    repo = request.app.state.repo
    alive = await repo.is_alive()
    count = await repo.triple_count() if alive else 0
    status_val = "ok" if alive else "degraded"
    code = 200 if alive else 503
    return JSONResponse(
        {"status": status_val, "oxigraph": "up" if alive else "down", "triples": count},
        status_code=code,
    )
