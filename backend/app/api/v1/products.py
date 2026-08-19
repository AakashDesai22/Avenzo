"""
AVENZO Backend — Product Master API Router (/api/v1/products)
"""

from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_roles
from app.models.user import User
from app.schemas.product import ProductCreate, ProductRead, ProductUpdate
from app.schemas.common import ApiResponse, PaginationMeta
from app.services import product_service

router = APIRouter(prefix="/products", tags=["Products"])


@router.get("", response_model=ApiResponse[List[ProductRead]])
async def list_products(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    category_id: Optional[UUID] = None,
    search: Optional[str] = None,
    barcode: Optional[str] = None,
    is_active: Optional[bool] = None,
    session: AsyncSession = Depends(get_db),
):
    """
    List products with pagination, category filter, barcode filter, and text search.
    """
    skip = (page - 1) * per_page
    products, total = await product_service.list_products(
        session, skip=skip, limit=per_page, category_id=category_id, search=search, barcode=barcode, is_active=is_active
    )
    total_pages = (total + per_page - 1) // per_page if per_page else 1

    return ApiResponse(
        success=True,
        data=[ProductRead.model_validate(p) for p in products],
        meta=PaginationMeta(
            page=page,
            per_page=per_page,
            total=total,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1,
        ),
    )


@router.get("/{product_id}", response_model=ApiResponse[ProductRead])
async def get_product(
    product_id: UUID,
    session: AsyncSession = Depends(get_db),
):
    """
    Get product details by ID.
    """
    product = await product_service.get_product_by_id(session, product_id)
    return ApiResponse(success=True, data=ProductRead.model_validate(product))


@router.post("", response_model=ApiResponse[ProductRead], status_code=status.HTTP_201_CREATED)
async def create_product(
    data: ProductCreate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["ADMIN", "BUSINESS_MANAGER"])),
):
    """
    Create a new Product Master entity (Admin/Manager only).
    """
    product = await product_service.create_product(session, data, created_by_id=current_user.id)
    return ApiResponse(
        success=True,
        data=ProductRead.model_validate(product),
        message="Product created successfully.",
    )


@router.put("/{product_id}", response_model=ApiResponse[ProductRead])
async def update_product(
    product_id: UUID,
    data: ProductUpdate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["ADMIN", "BUSINESS_MANAGER"])),
):
    """
    Update product master details (Admin/Manager only).
    """
    product = await product_service.update_product(session, product_id, data)
    return ApiResponse(
        success=True,
        data=ProductRead.model_validate(product),
        message="Product updated successfully.",
    )


@router.delete("/{product_id}", response_model=ApiResponse[ProductRead])
async def deactivate_product(
    product_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["ADMIN", "BUSINESS_MANAGER"])),
):
    """
    Deactivate product (Admin/Manager only).
    """
    product = await product_service.deactivate_product(session, product_id)
    return ApiResponse(
        success=True,
        data=ProductRead.model_validate(product),
        message="Product deactivated successfully.",
    )
