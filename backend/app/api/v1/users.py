"""
AVENZO Backend — User Management API Router (/api/v1/users)
"""

from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_roles
from app.models.user import User
from app.schemas.user import UserRead, UserUpdate, RoleRead
from app.schemas.common import ApiResponse
from app.services import user_service

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("", response_model=ApiResponse[List[UserRead]])
async def list_users(
    skip: int = 0,
    limit: int = 50,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["ADMIN", "BUSINESS_MANAGER"])),
):
    """
    List all registered users (Admin and Manager only).
    """
    users = await user_service.list_users(session, skip=skip, limit=limit)
    return ApiResponse(
        success=True,
        data=[UserRead.model_validate(u) for u in users],
    )


@router.get("/roles", response_model=ApiResponse[List[RoleRead]])
async def list_roles(
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["ADMIN", "BUSINESS_MANAGER"])),
):
    """
    List all system roles.
    """
    roles = await user_service.list_roles(session)
    return ApiResponse(
        success=True,
        data=[RoleRead.model_validate(r) for r in roles],
    )


@router.get("/{user_id}", response_model=ApiResponse[UserRead])
async def get_user(
    user_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get user profile by ID. Users can view their own profile; Admins/Managers can view any user.
    """
    user_role = current_user.role.name if current_user.role else ""
    if current_user.id != user_id and user_role not in ["ADMIN", "BUSINESS_MANAGER"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Cannot view another user's profile.",
        )

    user = await user_service.get_user_by_id(session, user_id)
    return ApiResponse(success=True, data=UserRead.model_validate(user))


@router.put("/{user_id}", response_model=ApiResponse[UserRead])
async def update_user(
    user_id: UUID,
    update_data: UserUpdate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["ADMIN", "BUSINESS_MANAGER"])),
):
    """
    Update user profile properties (Admin and Manager only).
    """
    user = await user_service.update_user(session, user_id, update_data)
    return ApiResponse(success=True, data=UserRead.model_validate(user), message="User updated successfully.")
