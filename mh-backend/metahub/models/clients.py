from pydantic import BaseModel

class Client(BaseModel):
    id: int | None = None
    name: str
    host: str

class Category(BaseModel):
    id: int | None = None
    name: str
    client: int