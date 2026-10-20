"""
AVENZO Backend — Product Master API Router (/api/v1/products)
"""

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import require_roles
from app.models.user import User
from app.schemas.common import ApiResponse, PaginationMeta
from app.schemas.product import ProductCreate, ProductRead, ProductUpdate
from app.services import product_service
from app.services.product_service import publish_product, unpublish_product

router = APIRouter(prefix="/products", tags=["Products"])


@router.get("", response_model=ApiResponse[list[ProductRead]])
async def list_products(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    category_id: UUID | None = None,
    search: str | None = None,
    barcode: str | None = None,
    is_active: bool | None = None,
    is_published: bool | None = None,
    session: AsyncSession = Depends(get_db),
):
    """
    List products with pagination, category filter, barcode filter, and text search.
    Use is_published=true to see only published products; is_published=false for drafts.
    """
    skip = (page - 1) * per_page
    products, total = await product_service.list_products(
        session,
        skip=skip,
        limit=per_page,
        category_id=category_id,
        search=search,
        barcode=barcode,
        is_active=is_active,
        is_published=is_published,
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
    Deactivate product (Admin/Manager only). Also unpublishes the product.
    """
    product = await product_service.deactivate_product(session, product_id)
    return ApiResponse(
        success=True,
        data=ProductRead.model_validate(product),
        message="Product deactivated and unpublished successfully.",
    )


@router.post("/{product_id}/publish", response_model=ApiResponse[ProductRead])
async def publish_product_endpoint(
    product_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["ADMIN", "BUSINESS_MANAGER"])),
):
    """
    Publish a product to make it visible in the consumer marketplace (Admin/Manager only).
    Product must be active. Drafts are hidden from consumers.
    """
    product = await publish_product(session, product_id)
    return ApiResponse(
        success=True,
        data=ProductRead.model_validate(product),
        message="Product published successfully. It is now visible in the consumer marketplace.",
    )


@router.post("/{product_id}/unpublish", response_model=ApiResponse[ProductRead])
async def unpublish_product_endpoint(
    product_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["ADMIN", "BUSINESS_MANAGER"])),
):
    """
    Revert a product to draft state (Admin/Manager only).
    The product remains in the admin catalogue but is hidden from consumer marketplace.
    """
    product = await unpublish_product(session, product_id)
    return ApiResponse(
        success=True,
        data=ProductRead.model_validate(product),
        message="Product unpublished. It is now hidden from the consumer marketplace.",
    )
