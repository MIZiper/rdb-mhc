from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class TagMeta(BaseModel):
    id: int
    name: str

class NodeMeta(BaseModel):
    id: str
    title: str
    description: str
    updated_at: datetime
    tag_ids: list[int]

class NodeDetail(NodeMeta):
    id: Optional[str] = None
    updated_at: Optional[datetime] = None
    backlink: str
    frozenlink: Optional[str] = None

class NodeResponse(BaseModel):
    items: list[NodeMeta]
    total: int