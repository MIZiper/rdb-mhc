"""Node metadata API schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class NodeMetaRead(BaseModel):
    id: UUID
    title: str
    description: Optional[str] = None
    updated_at: datetime
    tag_ids: list[int]
    data_type: Optional[str] = Field(None, description="Content type id")
    creator_name: Optional[str] = None
    creator_sub: Optional[str] = None
    status: str = Field("draft", description="draft | pending_review | published | archived")
    visibility: str = Field("public", description="Visibility label")


class NodeMetaList(BaseModel):
    items: list[NodeMetaRead]
    total: int


class NodeCreate(BaseModel):
    title: str
    description: str
    tag_ids: list[int] = []
    visibility: str = "public"


class NodeUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    tag_ids: Optional[list[int]] = None
    status: Optional[str] = None
    visibility: Optional[str] = None


class NodeStatusUpdate(BaseModel):
    status: str = Field(..., description="draft | pending_review | published | archived")

    @field_validator("status")
    @classmethod
    def _validate_status(cls, value: str) -> str:
        allowed = {"draft", "pending_review", "published", "archived"}
        if value not in allowed:
            raise ValueError(f"status must be one of: {', '.join(sorted(allowed))}")
        return value
