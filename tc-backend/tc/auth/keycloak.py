import os
import time
import logging
import httpx
from typing import Optional
from jose import jwt, JWTError
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

logger = logging.getLogger(__name__)

KC_SERVER_URL = os.getenv("KC_SERVER_URL", "")
KC_REALM = os.getenv("KC_REALM", "")
KC_CLIENT_ID = os.getenv("KC_CLIENT_ID", "")

_ISSUER = f"{KC_SERVER_URL.rstrip('/')}/realms/{KC_REALM}" if KC_SERVER_URL and KC_REALM else ""

_CERNS_CACHE: dict = {}
_CERNS_EXPIRY: float = 0.0
_CERNS_TTL = 3600.0

security = HTTPBearer(auto_error=False)


def _is_configured() -> bool:
    return bool(KC_SERVER_URL and KC_REALM and KC_CLIENT_ID)


def _get_certs_url() -> str:
    server = KC_SERVER_URL.rstrip("/")
    return f"{server}/realms/{KC_REALM}/protocol/openid-connect/certs"


async def _fetch_jwks() -> list[dict]:
    global _CERNS_CACHE, _CERNS_EXPIRY
    now = time.time()
    if _CERNS_CACHE and now < _CERNS_EXPIRY:
        return _CERNS_CACHE

    url = _get_certs_url()
    async with httpx.AsyncClient() as client:
        resp = await client.get(url)
        resp.raise_for_status()
        data = resp.json()
    keys = data.get("keys", [])
    _CERNS_CACHE = keys
    _CERNS_EXPIRY = now + _CERNS_TTL
    return keys


async def _decode_token(token: str) -> dict:
    if not _is_configured():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Keycloak is not configured",
        )
    jwks = await _fetch_jwks()
    try:
        unverified_header = jwt.get_unverified_header(token)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token header",
        )
    kid = unverified_header.get("kid")
    if not kid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing kid",
        )

    key_dict = None
    for k in jwks:
        if k.get("kid") == kid:
            key_dict = k
            break

    if key_dict is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Signing key not found",
        )

    try:
        payload = jwt.decode(
            token,
            key_dict,
            algorithms=[unverified_header.get("alg", "RS256")],
            issuer=_ISSUER,
            options={"verify_exp": True, "verify_aud": False, "verify_iss": True},
        )
    except JWTError as e:
        logger.warning("JWT decode failed: %s", e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    return payload


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> dict:
    if not _is_configured():
        return {"sub": "", "name": "Anonymous", "roles": []}
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    token = credentials.credentials
    payload = await _decode_token(token)
    sub = payload.get("sub")
    if not sub:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing sub claim",
        )
    name = payload.get("name") or payload.get("preferred_username") or sub

    resource_access = payload.get("resource_access", {})
    client_access = resource_access.get(KC_CLIENT_ID, {})
    client_roles = client_access.get("roles", [])

    realm_access = payload.get("realm_access", {})
    realm_roles = realm_access.get("roles", [])

    roles = list({*client_roles, *realm_roles})

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


def require_reviewer(user: dict = Depends(get_current_user)) -> dict:
    if "nodes:review" not in user.get("roles", []):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Reviewer role required",
        )
    return user
