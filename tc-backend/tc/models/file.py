from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class FileRead(BaseModel):
    id: UUID
    node_id: Optional[UUID] = None
    data_type: str
    original_name: Optional[str] = None
    mime_type: str
    size_bytes: int
    width: Optional[int] = None
    height: Optional[int] = None
    url: str = Field("", description="URL of the original file")
    thumb_url: str = Field("", description="URL of the thumbnail")
    creator_name: Optional[str] = None
    creator_sub: Optional[str] = None
    created_at: datetime
