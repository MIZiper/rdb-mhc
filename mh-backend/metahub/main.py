from fastapi import FastAPI
from metahub.db.connection import init_pool, close_pool, get_db

from metahub.api.tags import router as tags_router
from metahub.api.clients import router as client_router


async def lifespan(app: FastAPI):
    # podman run -it --rm -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=password -e POSTGRES_DB=metahub -v $(pwd)/metahub/db/:/docker-entrypoint-initdb.d/ -p 5432:5432 postgres
    await init_pool()
    yield
    await close_pool()


app = FastAPI(lifespan=lifespan, debug=True)

app.include_router(tags_router, prefix="/api")
app.include_router(client_router, prefix="/api")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app=app)
