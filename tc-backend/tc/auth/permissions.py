from fastapi import Depends, HTTPException, status
from typing import Optional

from tc.auth.provider import get_current_user

ROLE_READ_ALL = "nodes:read_all"
ROLE_CREATE = "nodes:create"
ROLE_EDIT_ANY = "nodes:edit_any"
ROLE_REVIEW = "nodes:review"

STATUS_DRAFT = "draft"
STATUS_PENDING_REVIEW = "pending_review"
STATUS_PUBLISHED = "published"
STATUS_ARCHIVED = "archived"

_STATUSES = {
    STATUS_DRAFT,
    STATUS_PENDING_REVIEW,
    STATUS_PUBLISHED,
    STATUS_ARCHIVED,
}
_REVIEW_TARGETS = {STATUS_DRAFT, STATUS_PUBLISHED, STATUS_ARCHIVED}


def require_role(role: str):
    async def checker(user: dict = Depends(get_current_user)) -> dict:
        if role not in user.get("roles", []):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{role}' required",
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
    if f"nodes:visibility:{visibility}" in user_roles:
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


def allowed_status_transition(
    user_roles: list[str],
    creator_sub: Optional[str],
    user_sub: str,
    current: str,
    target: str,
) -> bool:
    """Creators submit drafts; reviewers process pending reviews."""
    if target not in _STATUSES:
        return False
    if (
        can_edit_node(user_roles, creator_sub, user_sub)
        and current == STATUS_DRAFT
        and target == STATUS_PENDING_REVIEW
    ):
        return True
    return (
        ROLE_REVIEW in user_roles
        and current == STATUS_PENDING_REVIEW
        and target in _REVIEW_TARGETS
    )


def check_status_transition(
    user: dict,
    creator_sub: Optional[str],
    current: str,
    target: str,
) -> None:
    roles = user.get("roles", [])
    if allowed_status_transition(roles, creator_sub, user["sub"], current, target):
        return

    if ROLE_REVIEW in roles and current == STATUS_PENDING_REVIEW:
        detail = (
            "Reviewers can only move pending_review nodes to "
            "draft, published or archived"
        )
    elif can_edit_node(roles, creator_sub, user["sub"]) and current == STATUS_DRAFT:
        detail = "Creators can only submit draft nodes for review"
    else:
        detail = "You are not authorized to change this node status"
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


def check_status_edit_allowed(user: dict, node_status: Optional[str]) -> None:
    """Only drafts are editable; non-draft nodes require edit_any."""
    if node_status == STATUS_DRAFT:
        return
    roles = user.get("roles", [])
    if ROLE_EDIT_ANY in roles:
        return
    raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail="Only draft nodes can be edited",
    )
