"""Runtime configuration exposed to the frontend (Keycloak + MetaHub)."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from tc.auth.provider import get_optional_user
from tc.settings import settings

router = APIRouter(prefix="/config")


@router.get("")
async def get_config(user=Depends(get_optional_user)):
    config = {
        "kc_url": settings.keycloak_url_public,
        "kc_realm": settings.keycloak_realm,
        "kc_client_id": settings.keycloak_client_id,
        "mh_host": settings.metahub_host,
    }
    if user is not None:
        config["user_roles"] = list(user.get("roles", []))
        config["user_sub"] = user["sub"]
        config["user_name"] = user["name"]
    return config
