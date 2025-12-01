from typing import Optional
from pydantic import BaseModel

class TagCreateUpdate(BaseModel):
    name: str
    exposed: bool

class TagRead(TagCreateUpdate):
    id: int
    category_id: int