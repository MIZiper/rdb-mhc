import os
import httpx
from typing import Optional

METAHUB_HOST = os.getenv("TC_METAHUB", "localhost:8033")

_client: httpx.AsyncClient | None = None


def get_mh_client() -> httpx.AsyncClient:
    global _client
    if _client is None:
        _client = httpx.AsyncClient(timeout=30.0)
    return _client


async def close_mh_client():
    global _client
    if _client:
        await _client.aclose()
        _client = None


def get_metahub_url(path: str) -> str:
    host = METAHUB_HOST
    if not host.startswith("http"):
        host = f"http://{host}"
    return f"{host}{path}"


async def expand_tag_ids(tag_ids: list[int]) -> list[int]:
    client = get_mh_client()
    url = get_metahub_url("/api/search/expand")
    try:
        resp = await client.post(url, json=tag_ids)
        resp.raise_for_status()
        return resp.json()
    except Exception:
        return list(tag_ids)


async def fetch_tag_relationships(
    tag_ids: list[int],
) -> dict[int, dict]:
    client = get_mh_client()
    url = get_metahub_url("/api/tags/search")
    try:
        resp = await client.post(url, json=tag_ids)
        resp.raise_for_status()
        items = resp.json()
        return {t["id"]: t for t in items}
    except Exception:
        return {tid: {"id": tid, "name": f"Tag #{tid}"} for tid in tag_ids}


async def fetch_tags_with_parent(
    category_id: int,
) -> list[dict]:
    client = get_mh_client()
    url = get_metahub_url(
        f"/api/tags/with-parent?category_id={category_id}"
    )
    try:
        resp = await client.get(url)
        resp.raise_for_status()
        return resp.json()
    except Exception:
        return []


async def deep_search(
    tag_ids: list[int],
    include_descendants: bool = True,
    include_bound_nodes: bool = True,
) -> dict:
    client = get_mh_client()
    url = get_metahub_url("/api/search/deep")
    try:
        resp = await client.post(
            url,
            json={
                "tag_ids": tag_ids,
                "include_descendants": include_descendants,
                "include_bound_nodes": include_bound_nodes,
            },
        )
        resp.raise_for_status()
        return resp.json()
    except Exception:
        return {
            "expanded_tag_ids": tag_ids,
            "bound_node_ids": [],
        }
