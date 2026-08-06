from typing import Callable, Set
from fastapi import Depends, HTTPException, status
from app.core.deps import get_current_user
from app.modules.users.models import User

# Role Constants
ROLE_USER = "USER"
ROLE_ADMIN = "ADMIN"

# Permission Constants
PERM_MANAGE_USERS = "manage_users"
PERM_MANAGE_POIS = "manage_pois"
PERM_MANAGE_SYSTEM = "manage_system"
PERM_MANAGE_EVENTS = "manage_events"
PERM_MANAGE_MISSIONS = "manage_missions"

ROLE_PERMISSIONS: dict[str, Set[str]] = {
    ROLE_ADMIN: {
        PERM_MANAGE_USERS,
        PERM_MANAGE_POIS,
        PERM_MANAGE_SYSTEM,
        PERM_MANAGE_EVENTS,
        PERM_MANAGE_MISSIONS,
    },
    ROLE_USER: set(),
}


def has_permission(user_role: str, permission: str) -> bool:
    role_perms = ROLE_PERMISSIONS.get(user_role.upper(), set())
    return permission in role_perms


def require_role(required_role: str) -> Callable:
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role.upper() != required_role.upper():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"دسترسی غیرمجاز. نقش {required_role} الزامی است.",
            )
        return current_user

    return role_checker


def require_permission(required_permission: str) -> Callable:
    def permission_checker(current_user: User = Depends(get_current_user)) -> User:
        if not has_permission(current_user.role, required_permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"دسترسی غیرمجاز. مجوز '{required_permission}' الزامی است.",
            )
        return current_user

    return permission_checker
