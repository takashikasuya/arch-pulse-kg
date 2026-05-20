"""FastAPI application factory for CS-KG-GEOM."""
from __future__ import annotations
from contextlib import asynccontextmanager
from fastapi import FastAPI

from .adapters.mem_geom import MemGeomRepository
from .ports.geom_repository import GeomRepository
from .routers import health, geom


def create_app(repo: GeomRepository | None = None) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.repo = repo or MemGeomRepository()
        yield

    app = FastAPI(title="CS-KG-GEOM", version="0.1.0", lifespan=lifespan)
    app.include_router(health.router)
    app.include_router(geom.router)
    return app
