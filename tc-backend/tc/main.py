from fastapi import FastAPI
from tc.db.connection import init_pool, close_pool
import os

from tc.api.node_op import router as node_router

metahub_host = os.getenv("TC_METAHUB", "localhost:8033")


async def lifespan(app: FastAPI):
    await init_pool()
    yield
    await close_pool()


app = FastAPI(lifespan=lifespan, debug=True)

app.include_router(node_router, prefix="/api")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app=app)
