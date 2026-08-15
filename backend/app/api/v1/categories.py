"""
AVENZO Backend — Category API Router (/api/v1/categories)
"""

from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_roles
from app.models.user import User
from app.schemas.category import CategoryCreate, CategoryRead, CategoryUpdate
from app.schemas.common import ApiResponse
from app.services import category_service

router = APIRouter(prefix="/categories", tags=["Categories"])


@router.get("", response_model=ApiResponse[List[CategoryRead]])
async def list_categories(
    active_only: bool = True,
    session: AsyncSession = Depends(get_db),
):
    """
    List all product categories.
    """
    categories = await category_service.list_categories(session, active_only=active_only)
    return ApiResponse(
        success=True,
        data=[CategoryRead.model_validate(c) for c in categories],
    )


@router.get("/{category_id}", response_model=ApiResponse[CategoryRead])
async def get_category(
    category_id: UUID,
    session: AsyncSession = Depends(get_db),
):
    """
    Get category details by ID.
    """
    category = await category_service.get_category_by_id(session, category_id)
    return ApiResponse(success=True, data=CategoryRead.model_validate(category))


@router.post("", response_model=ApiResponse[CategoryRead], status_code=status.HTTP_201_CREATED)
async def create_category(
    data: CategoryCreate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["ADMIN", "BUSINESS_MANAGER"])),
):
    """
    Create a new product category (Admin/Manager only).
    """
    category = await category_service.create_category(session, data)
    return ApiResponse(
        success=True,
        data=CategoryRead.model_validate(category),
        message="Category created successfully.",
    )


@router.put("/{category_id}", response_model=ApiResponse[CategoryRead])
async def update_category(
    category_id: UUID,
    data: CategoryUpdate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["ADMIN", "BUSINESS_MANAGER"])),
):
    """
    Update category (Admin/Manager only).
    """
    category = await category_service.update_category(session, category_id, data)
    return ApiResponse(
        success=True,
        data=CategoryRead.model_validate(category),
        message="Category updated successfully.",
    )


@router.delete("/{category_id}", response_model=ApiResponse[CategoryRead])
async def deactivate_category(
    category_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["ADMIN", "BUSINESS_MANAGER"])),
):
    """
    Deactivate a category (Admin/Manager only).
    """
    category = await category_service.deactivate_category(session, category_id)
    return ApiResponse(
        success=True,
        data=CategoryRead.model_validate(category),
        message="Category deactivated successfully.",
    )
