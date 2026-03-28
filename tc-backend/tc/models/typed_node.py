from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional, Literal, Any
from uuid import UUID
import json



class TableData(BaseModel):
    type: Literal["table"] = "table"
    columns: list[dict[str, Any]] = Field(..., description="Column definitions")
    rows: list[dict[str, Any]] = Field(..., description="Row data")


class ImageData(BaseModel):
    type: Literal["image"] = "image"
    format: Literal["base64", "url"] = Field(..., description="Image format")
    data: str = Field(..., description="Image data (base64 string or URL)")
    mime_type: Optional[str] = Field(None, description="MIME type for the image")


class GenericData(BaseModel):
    type: Literal["generic"] = "generic"
    content: dict[str, Any] = Field(..., description="Generic JSON content")


NodeData = TableData | ImageData | GenericData



class NodeDataPayload(BaseModel):
    content: NodeData = Field(..., description="Node data payload")

    @field_validator("content", mode="before")
    @classmethod
    def validate_size(cls, v):
        serialized = json.dumps(v)
        max_size = 10 * 1024 * 1024
        if len(serialized.encode("utf-8")) > max_size:
            raise ValueError(f"Data payload exceeds maximum size of 10MB")
        return v



class NodeDataRead(BaseModel):
    id: UUID
    content: NodeData
    data_type: str
    updated_at: datetime