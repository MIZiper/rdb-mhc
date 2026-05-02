from pydantic import BaseModel
from typing import Optional
from uuid import UUID


class NodeRegistrationCreate(BaseModel):
    tag_id: int
    client_id: int
    client_node_id: UUID
    node_tag_ids: list[int] = []
    description: Optional[str] = None
    link: Optional[str] = None


class NodeRegistrationRead(BaseModel):
    tag_id: int
    client_id: int
    client_node_id: UUID
    node_tag_ids: list[int]
    params: dict


class NodeRegistrationList(BaseModel):
    items: list[NodeRegistrationRead]
    total: int


class TagDescendant(BaseModel):
    id: int
    name: str
    parent_id: Optional[int] = None


class DeepSearchRequest(BaseModel):
    tag_ids: list[int]
    include_descendants: bool = True
    include_bound_nodes: bool = True


class DeepSearchResult(BaseModel):
    expanded_tag_ids: list[int]
    bound_node_ids: list[dict]
