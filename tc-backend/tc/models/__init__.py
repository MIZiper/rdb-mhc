from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional, Literal, Any
from uuid import UUID

class TagMeta(BaseModel):
    id: int
    name: str

class NodeMetaRead(BaseModel):
    id: UUID
    title: str
    description: str
    updated_at: datetime
    tag_ids: list[int]
    data_type: Optional[str] = Field(
        None, description="Type of data stored"
    )

class NodeDetailRead(NodeMetaRead):
    data: dict
    backlink: Optional[str] = None
    frozenlink: Optional[str] = None

class NodeCreate(BaseModel):
    title: str
    description: str
    tag_ids: list[int] = []

class NodeUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    tag_ids: Optional[list[int]] = None

class NodeMetaList(BaseModel):
    items: list[NodeMetaRead]
    total: int