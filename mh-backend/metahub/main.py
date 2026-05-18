from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from metahub.db.connection import init_pool, close_pool, get_db

from metahub.api.tags import router as tags_router
from metahub.api.clients import router as client_router
from metahub.api.node_registration import router as node_router
from metahub.services.tc_client import close_tc_client


async def lifespan(app: FastAPI):
    await init_pool()
    yield
    await close_pool()
    await close_tc_client()

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        f"http://localhost:{p}" # frontend dev
        for p in range(5130, 5140)
    ] + [
        f"http://localhost:{p}" # backend dev
        for p in range(8030, 8040)
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(tags_router, prefix="/api")
app.include_router(client_router, prefix="/api")
app.include_router(node_router, prefix="/api")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app=app)
