"""API routers, aggregated under the ``/api`` prefix."""

from __future__ import annotations

from fastapi import APIRouter

from tc.routes import admin, config, files, permissions, types
from tc.routes.nodes import content, meta, push, query, state

api_router = APIRouter()

# Node metadata and content first so the specific ``/nodes/data`` and
# ``/nodes/fields`` routes are not shadowed (they are distinct paths, but
# keeping a stable order avoids surprises).
api_router.include_router(config.router)
api_router.include_router(permissions.router)
api_router.include_router(meta.router)
api_router.include_router(content.router)
api_router.include_router(state.router)
api_router.include_router(push.router)
api_router.include_router(query.router)
api_router.include_router(files.router)
api_router.include_router(types.router)
api_router.include_router(admin.router)
