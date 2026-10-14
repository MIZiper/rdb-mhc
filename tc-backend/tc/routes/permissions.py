"""Current user permissions."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from tc.auth.provider import get_optional_user

router = APIRouter(prefix="/permissions")


@router.get("")
async def get_my_permissions(user=Depends(get_optional_user)):
    if user is None:
        return {"authenticated": False, "roles": []}
    return {
        "authenticated": True,
        "sub": user["sub"],
        "name": user["name"],
        "roles": user.get("roles", []),
    }
