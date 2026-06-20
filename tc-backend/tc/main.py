from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from tc.db.connection import init_pool, close_pool
from tc.auth.keycloak import get_optional_user
import os

from tc.api.node_op import router as node_router
from tc.api.node_typed import router as typed_router
from tc.api.node_push import router as push_router
from tc.api.config import router as config_router
from tc.services.metahub_client import close_mh_client

metahub_host = os.getenv("TC_METAHUB", "localhost:8033")


async def lifespan(app: FastAPI):
    await init_pool()
    yield
    await close_pool()
    await close_mh_client()


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        f"http://localhost:{p}"
        for p in range(5130, 5140)
    ] + [
        f"http://localhost:{p}"
        for p in range(8030, 8040)
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(config_router, prefix="/api")
app.include_router(node_router, prefix="/api")
app.include_router(typed_router, prefix="/api")
app.include_router(push_router, prefix="/api")

from fastapi import APIRouter

permissions_router = APIRouter(prefix="/permissions")


@permissions_router.get("")
async def get_my_permissions(
    user=Depends(get_optional_user),
):
    if user is None:
        return {"authenticated": False, "roles": []}
    return {
        "authenticated": True,
        "sub": user["sub"],
        "name": user["name"],
        "roles": user.get("roles", []),
    }


app.include_router(permissions_router, prefix="/api")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app=app)
