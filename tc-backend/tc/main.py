from fastapi import FastAPI
from tc.db.connection import init_pool, close_pool
import os

from tc.api.node_op import router as node_router
from tc.api.node_typed import router as typed_router

metahub_host = os.getenv("TC_METAHUB", "localhost:8033")


async def lifespan(app: FastAPI):
    await init_pool()
    yield
    await close_pool()


app = FastAPI(lifespan=lifespan)

app.include_router(node_router, prefix="/api")
app.include_router(typed_router, prefix="/api")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app=app)
