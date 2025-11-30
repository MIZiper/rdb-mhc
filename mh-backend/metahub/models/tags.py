from typing import Optional
from pydantic import BaseModel

class Tag(BaseModel):
    id: Optional[int] = None
    name: str
    category_id: int
    exposed: bool