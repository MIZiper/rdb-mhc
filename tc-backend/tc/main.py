from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from tc.db.connection import init_pool, close_pool
import os

from tc.api.node_op import router as node_router
from tc.api.node_typed import router as typed_router
from tc.api.node_push import router as push_router
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
        for p in range(5170, 5180)
    ] + [
        f"http://localhost:{p}"
        for p in range(8030, 8040)
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(node_router, prefix="/api")
app.include_router(typed_router, prefix="/api")
app.include_router(push_router, prefix="/api")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app=app)
