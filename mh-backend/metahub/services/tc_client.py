import os
import httpx
from uuid import UUID

METAHUB_HOST = os.getenv("TC_METAHUB", "localhost:8033")

_client: httpx.AsyncClient | None = None


def get_tc_client() -> httpx.AsyncClient:
    global _client
    if _client is None:
        _client = httpx.AsyncClient(timeout=30.0)
    return _client


async def close_tc_client():
    global _client
    if _client:
        await _client.aclose()
        _client = None


async def fetch_tc_nodes_by_tags(
    client_host: str,
    tag_ids: list[int],
    mode: str = "exact",
    limit: int | None = None,
) -> list[dict]:
    client = get_tc_client()
    url = f"http://{client_host}/api/nodes/by_tags"
    params = {"mode": mode}
    if limit:
        params["limit"] = limit
    try:
        resp = await client.post(url, json=tag_ids, params=params)
        resp.raise_for_status()
        data = resp.json()
        return data.get("items", [])
    except Exception:
        return []


async def fetch_tc_node_meta(
    client_host: str, node_id: UUID
) -> dict | None:
    client = get_tc_client()
    url = f"http://{client_host}/api/nodes/{node_id}/meta"
    try:
        resp = await client.get(url)
        resp.raise_for_status()
        return resp.json()
    except Exception:
        return None
