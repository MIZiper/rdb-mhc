from fastapi import FastAPI

async def lifespan(app: FastAPI):
    yield

app = FastAPI(lifespan=lifespan, debug=True)

if __name__=="__main__":
    import uvicorn
    uvicorn.run(app=app)