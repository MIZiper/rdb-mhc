from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from uuid import UUID

class TagMeta(BaseModel):
    id: int
    name: str

class NodeMeta(BaseModel):
    id: UUID
    title: str
    description: str
    updated_at: datetime
    tag_ids: list[int]

class NodeDetail(NodeMeta):
    id: Optional[UUID] = None
    updated_at: Optional[datetime] = None
    backlink: str
    frozenlink: Optional[str] = None

class NodeResponse(BaseModel):
    items: list[NodeMeta]
    total: int