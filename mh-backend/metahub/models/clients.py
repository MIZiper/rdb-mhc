from pydantic import BaseModel
from typing import Optional

class ClientCreateUpdate(BaseModel):
    name: str
    host: Optional[str] = None

class ClientRead(ClientCreateUpdate):
    id: int

class CategoryCreateUpdate(BaseModel):
    name: str

class CategoryRead(CategoryCreateUpdate):
    id: int
    client_id: int