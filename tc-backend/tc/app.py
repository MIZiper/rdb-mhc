"""FastAPI application factory."""

from __future__ import annotations

import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from tc.content_types.seed import seed_data_types
from tc.db import connection
from tc.db.schema import ensure_schema
from tc.routes import api_router
from tc.services.metahub import close_client
from tc.settings import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Vite dev servers for the tc frontend (5130-5139) and MetaHub (8030-8039).
_DEV_CORS_ORIGINS = [
    f"http://localhost:{port}" for port in (*range(5130, 5140), *range(8030, 8040))
]


async def lifespan(app: FastAPI) -> None:
    await connection.init_pool()
    if connection.pool is not None:
        async with connection.pool.acquire() as conn:
            await ensure_schema(conn)
            await seed_data_types(conn)
    yield
    await connection.close_pool()
    await close_client()


def create_app() -> FastAPI:
    app = FastAPI(lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_DEV_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(api_router, prefix="/api")
    _mount_frontend(app)
    return app


def _mount_frontend(app: FastAPI) -> None:
    """Serve the built SPA when ``FRONTEND_DIST`` points at a directory."""
    dist = settings.frontend_dist
    if not dist or not os.path.isdir(dist):
        return

    app.mount("/static", StaticFiles(directory=dist), name="static")

    @app.get("/")
    def serve_index():
        return FileResponse(os.path.join(dist, "index.html"))

    @app.get("/{full_path:path}")
    def serve_spa(full_path: str):
        file_path = os.path.join(dist, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(dist, "index.html"))


app = create_app()
