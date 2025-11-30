from pydantic import BaseModel
from typing import Optional

class Client(BaseModel):
    id: Optional[int] = None # None when creating a new client
    name: str
    host: Optional[str] = None

class Category(BaseModel):
    id: Optional[int] = None
    name: str
    client_id: Optional[int] = None