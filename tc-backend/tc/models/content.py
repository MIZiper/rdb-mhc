"""Node content API schemas.

Content is arbitrary JSON. Per-type structure is described by the
``tc.content_types`` descriptors (and optionally validated against a JSON
Schema), not by a hand-maintained union of Python models.
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

MAX_CONTENT_BYTES = 10 * 1024 * 1024


class ContentPayload(BaseModel):
    content: Any = Field(..., description="Node content, any JSON value")
    data_type: Optional[str] = Field(
        None, description="Content type id; falls back to content['type']"
    )

    @field_validator("content", mode="before")
    @classmethod
    def _validate_size(cls, value: Any) -> Any:
        serialized = json.dumps(value)
        if len(serialized.encode("utf-8")) > MAX_CONTENT_BYTES:
            raise ValueError("Data payload exceeds maximum size of 10MB")
        return value


class NodeContentRead(BaseModel):
    id: UUID
    title: str
    description: Optional[str] = None
    updated_at: datetime
    content: Any
    data_type: Optional[str] = None
    tag_ids: list[int] = Field(default_factory=list)
    creator_name: Optional[str] = None
    creator_sub: Optional[str] = None
    status: str = "draft"
    visibility: str = "public"
    source_system: Optional[str] = None
    source_id: Optional[str] = None
    source_part: Optional[str] = None
    source_url: Optional[str] = None
    source_linked_at: Optional[datetime] = None
    source_linked_by: Optional[str] = None


class NodeContentCreate(BaseModel):
    title: str
    description: str
    content: Any
    data_type: str
    tag_ids: list[int] = Field(default_factory=list)
    visibility: str = "public"
