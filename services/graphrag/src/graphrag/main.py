"""CS-AI-GRAPHRAG FastAPI application factory."""
from __future__ import annotations
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI

from .config import settings
from .ports.kg_reader import KgReader
from .ports.ts_reader import TsReader
from .ports.llm_gateway import LlmGateway
from .adapters.null_ts_reader import NullTsReader
from .adapters.null_llm_gateway import NullLlmGateway
from .routers import health, analysis

logger = logging.getLogger(__name__)


def create_app(
    kg: KgReader | None = None,
    ts: TsReader | None = None,
    llm: LlmGateway | None = None,
) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        if kg is None:
            from .adapters.sparql_http import SparqlHttpClient
            _kg = SparqlHttpClient(settings.kg_store_url)
        else:
            _kg = kg

        if ts is None:
            if settings.ts_db_url:
                from .adapters.timescale_http import TimescaleHttpClient
                _ts: TsReader = TimescaleHttpClient(settings.ts_db_url)
            else:
                logger.warning("TS_DB_URL not set — using NullTsReader (degraded mode)")
                _ts = NullTsReader()
        else:
            _ts = ts

        _llm = llm or NullLlmGateway()

        app.state.kg = _kg
        app.state.ts = _ts
        app.state.llm = _llm
        yield
        if hasattr(_kg, "aclose"):
            await _kg.aclose()
        if hasattr(_ts, "aclose"):
            await _ts.aclose()

    app = FastAPI(title="CS-AI-GRAPHRAG", version="0.1.0", lifespan=lifespan)
    app.include_router(health.router)
    app.include_router(analysis.router)
    return app


app = create_app()
