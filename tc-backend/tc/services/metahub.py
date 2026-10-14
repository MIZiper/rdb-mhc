"""HTTP client for the MetaHub tag service.

TC stores node data and tag ids; MetaHub owns tag relationships. These
helpers resolve/expand tags and back the cross-type search.
"""

from __future__ import annotations

from typing import Optional

import httpx

from tc.settings import settings

_client: Optional[httpx.AsyncClient] = None


def get_client() -> httpx.AsyncClient:
    global _client
    if _client is None:
        _client = httpx.AsyncClient(timeout=30.0)
    return _client


async def close_client() -> None:
    global _client
    if _client is not None:
        await _client.aclose()
        _client = None


def _url(path: str) -> str:
    host = settings.metahub_host
    if not host.startswith("http"):
        host = f"http://{host}"
    return f"{host}{path}"


async def expand_tag_ids(tag_ids: list[int]) -> list[int]:
    """Return the given tags plus their descendants."""
    try:
        resp = await get_client().post(_url("/api/tags/expand"), json=tag_ids)
        resp.raise_for_status()
        return resp.json()
    except Exception:
        return list(tag_ids)


