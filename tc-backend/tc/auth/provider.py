"""Keycloak JWT authentication.

Decodes bearer tokens against the realm's JWKS and extracts the user's
identity plus the union of realm and client roles.
"""

from __future__ import annotations

import time
from typing import Any, Optional

import httpx
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from tc.settings import settings

_CERTS_TTL = 3600.0
_certs_cache: list[dict] = []
_certs_expiry: float = 0.0

security = HTTPBearer(auto_error=False)


def is_configured() -> bool:
    return bool(settings.kc_server_url and settings.kc_realm and settings.kc_client_id)


def _certs_url() -> str:
    server = settings.kc_server_url.rstrip("/")
    return f"{server}/realms/{settings.kc_realm}/protocol/openid-connect/certs"


async def _fetch_jwks() -> list[dict]:
    global _certs_cache, _certs_expiry
    now = time.time()
    if _certs_cache and now < _certs_expiry:
        return _certs_cache
    async with httpx.AsyncClient() as client:
        resp = await client.get(_certs_url())
        resp.raise_for_status()
        data = resp.json()
    _certs_cache = data.get("keys", [])
    _certs_expiry = now + _CERTS_TTL
    return _certs_cache


async def _decode_token(token: str) -> dict[str, Any]:
    if not is_configured():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Keycloak is not configured",
        )
    jwks = await _fetch_jwks()
    try:
        header = jwt.get_unverified_header(token)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token header"
        )

    kid = header.get("kid")
    if not kid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token missing kid"
        )

    key = next((k for k in jwks if k.get("kid") == kid), None)
    if key is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Signing key not found"
        )

    try:
        return jwt.decode(
            token,
            key,
            algorithms=[header.get("alg", "RS256")],
            issuer=settings.kc_issuer,
            options={"verify_exp": True, "verify_aud": False, "verify_iss": True},
        )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token"
        )


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> dict:
    if not is_configured():
        return {"sub": "", "name": "Anonymous", "roles": []}
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated"
        )

    payload = await _decode_token(credentials.credentials)
    sub = payload.get("sub")
    if not sub:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token missing sub claim"
        )

    client_roles = (
        payload.get("resource_access", {}).get(settings.kc_client_id, {}).get("roles", [])
    )
    realm_roles = payload.get("realm_access", {}).get("roles", [])
    roles = list({*client_roles, *realm_roles})
    name = payload.get("name") or payload.get("preferred_username") or sub
    return {"sub": sub, "name": name, "roles": roles}


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[dict]:
    if credentials is None:
        return None
    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None
