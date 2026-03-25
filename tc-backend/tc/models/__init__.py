from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional, Literal, Any
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
    data_type: Optional[str] = Field(
        None, description="Type of data stored (table, image, generic)"
    )

class NodeDetail(NodeMeta):
    id: Optional[UUID] = None
    updated_at: Optional[datetime] = None
    backlink: Optional[str] = None
    frozenlink: Optional[str] = None

class NodeResponse(BaseModel):
    items: list[NodeMeta]
    total: int