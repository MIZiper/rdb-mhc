"""Request models for cross-type query and aggregation."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, Field

TagMode = Literal["exact", "ancestors"]
FilterOp = Literal["eq", "ne", "gt", "gte", "lt", "lte", "contains"]
AggFunc = Literal["count", "avg", "min", "max", "sum"]


class QueryFilter(BaseModel):
    key: str = Field(..., description="Canonical field key")
    op: FilterOp = "eq"
    value: Any = None


class NodeQuery(BaseModel):
    text: Optional[str] = None
    types: Optional[list[str]] = None
    tag_ids: list[int] = Field(default_factory=list)
    tag_mode: TagMode = "exact"
    filters: list[QueryFilter] = Field(default_factory=list)
    status: Optional[str] = None
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=200)


class AggregateRequest(BaseModel):
    types: Optional[list[str]] = None
    tag_ids: list[int] = Field(default_factory=list)
    tag_mode: TagMode = "exact"
    filters: list[QueryFilter] = Field(default_factory=list)
    status: Optional[str] = None
    group_by: list[str] = Field(
        default_factory=list, description="Canonical keyword field keys to group by"
    )
    group_by_tag: bool = Field(
        False, description="Additionally group results by tag id"
    )
    metric: Optional[str] = Field(
        None, description="Canonical numeric field key to aggregate"
    )
    func: AggFunc = "count"
