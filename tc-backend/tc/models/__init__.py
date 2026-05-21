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
    creator_name: Optional[str] = Field(
        None, description="Display name of the creator"
    )
    creator_sub: Optional[str] = Field(
        None, description="Keycloak sub of the creator"
    )
    status: str = Field(
        "draft", description="Item status: draft, pending_review, published, archived"
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
    status: Optional[str] = Field(
        None, description="Item status: draft, pending_review, published, archived"
    )

class NodeStatusUpdate(BaseModel):
    status: str = Field(
        ..., description="New status: draft, pending_review, published, archived"
    )

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        allowed = {"draft", "pending_review", "published", "archived"}
        if v not in allowed:
            raise ValueError(f"status must be one of: {', '.join(sorted(allowed))}")
        return v

class NodeMetaList(BaseModel):
    items: list[NodeMetaRead]
    total: int