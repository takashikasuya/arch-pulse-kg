"""CS-KG-STORE — FastAPI application factory."""
import importlib.resources
import logging
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI

from .config import settings
from .ports.triplestore import TriplestoreRepository
from .ports.events import ChangeEventPublisher
from .routers import health, sparql, shacl, bir, catalog

logger = logging.getLogger(__name__)


def _load_bir_shapes() -> str:
    pkg = importlib.resources.files("kg_store.shacl")
    return (pkg / "bir_shapes.ttl").read_text()


def create_app(
    repo: TriplestoreRepository | None = None,
    publisher: ChangeEventPublisher | None = None,
) -> FastAPI:
    _shapes_ttl = _load_bir_shapes()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        if repo is None:
            from .adapters.oxigraph_http import OxigraphHttpRepository

            r = OxigraphHttpRepository(settings.sparql_endpoint)
            app.state.repo = r
        else:
            app.state.repo = repo

        if publisher is None:
            try:
                import nats as nats_lib

                nc = await nats_lib.connect(settings.nats_url)
                from .adapters.nats_publisher import NatsJetStreamPublisher

                app.state.publisher = NatsJetStreamPublisher(nc, settings.nats_stream)
                logger.info("Connected to NATS at %s", settings.nats_url)
            except Exception:
                logger.warning("NATS unavailable — using NullPublisher")
                from .adapters.null_publisher import NullPublisher

                app.state.publisher = NullPublisher()
        else:
            app.state.publisher = publisher

        app.state.bir_shapes_ttl = _shapes_ttl
        logger.info("CS-KG-STORE startup complete")
        yield
        await app.state.repo.aclose()
        await app.state.publisher.aclose()

    app = FastAPI(
        title="CS-KG-STORE",
        version="0.1.0",
        description="Knowledge Graph Store — SPARQL 1.1/SPARQL-star + bir_id + DCAT catalog",
        lifespan=lifespan,
    )
    app.include_router(health.router)
    app.include_router(sparql.router)
    app.include_router(shacl.router)
    app.include_router(bir.router)
    app.include_router(catalog.router)
    return app


app = create_app()
