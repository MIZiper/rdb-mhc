from fastapi import Depends, HTTPException, status
from typing import Optional

from tc.auth.keycloak import get_current_user

ROLE_READ_ALL = "nodes:read_all"
ROLE_CREATE = "nodes:create"
ROLE_EDIT_ANY = "nodes:edit_any"
ROLE_REVIEW = "nodes:review"


def has_role(user: dict, role: str) -> bool:
    return role in user.get("roles", [])


def require_role(role: str):
    async def checker(user: dict = Depends(get_current_user)) -> dict:
        if not has_role(user, role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{role}' required",
            )
        return user

    return checker


def require_any_role(*roles: str):
    async def checker(user: dict = Depends(get_current_user)) -> dict:
        user_roles = set(user.get("roles", []))
        if not user_roles.intersection(roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"One of {roles} required",
            )
        return user

    return checker


def can_see_node(
    user_roles: list[str],
    visibility: str,
    creator_sub: Optional[str],
    user_sub: str,
) -> bool:
    if ROLE_READ_ALL in user_roles:
        return True
    if visibility == "public":
        return True
    if visibility in user_roles:
        return True
    if creator_sub == user_sub:
        return True
    return False


def can_edit_node(
    user_roles: list[str],
    creator_sub: Optional[str],
    user_sub: str,
) -> bool:
    if ROLE_EDIT_ANY in user_roles:
        return True
    if creator_sub is not None and creator_sub == user_sub:
        return True
    return False


def check_edit_node(
    user: dict,
    creator_sub: Optional[str],
) -> None:
    if not can_edit_node(user.get("roles", []), creator_sub, user["sub"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to edit this node",
        )
