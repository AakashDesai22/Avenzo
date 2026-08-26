"""
AVENZO Backend — Consumer Marketplace API Router (/api/v1/marketplace)
Provides consumer-facing product catalog, search, and availability endpoints.
"""

from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.marketplace import MarketplaceProductRead
from app.schemas.common import ApiResponse, PaginationMeta
from app.services import marketplace_service

router = APIRouter(prefix="/marketplace", tags=["Consumer Marketplace"])


@router.get("/products", response_model=ApiResponse[List[MarketplaceProductRead]])
async def list_marketplace_products(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    category_id: Optional[UUID] = None,
    search: Optional[str] = None,
    in_stock_only: bool = Query(default=False),
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List consumer marketplace products with aggregate availability.
    Accessible by authenticated consumers and users.
    """
    skip = (page - 1) * per_page
    items, total = await marketplace_service.list_marketplace_products(
        session,
        skip=skip,
        limit=per_page,
        category_id=category_id,
        search=search,
        in_stock_only=in_stock_only,
    )
    total_pages = (total + per_page - 1) // per_page if per_page else 1

    return ApiResponse(
        success=True,
        data=items,
        meta=PaginationMeta(
            page=page,
            per_page=per_page,
            total=total,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1,
        ),
    )


@router.get("/products/{product_id}", response_model=ApiResponse[MarketplaceProductRead])
async def get_marketplace_product(
    product_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get detailed consumer marketplace product information including availability status.
    Returns 404 if product does not exist, is inactive, or is deleted.
    """
    product = await marketplace_service.get_marketplace_product_by_id(session, product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Marketplace product with ID '{product_id}' not found.",
        )
    return ApiResponse(success=True, data=product)
