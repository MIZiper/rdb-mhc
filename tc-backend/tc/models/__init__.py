from pydantic import BaseModel
from datetime import datetime

class TagMeta(BaseModel):
    id: int
    name: str

class NodeMeta(BaseModel):
    id: str
    title: str
    description: str
    updated_at: datetime
    tags: list[TagMeta]

class NodeDetail(NodeMeta):
    backlink: str
    frozenlink: str