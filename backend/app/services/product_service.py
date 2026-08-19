"""
AVENZO Backend — Product Service
Business logic for managing Product Master catalogue.
"""

from typing import List, Optional, Tuple
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from sqlalchemy import func
from fastapi import HTTPException, status

from app.models.product import Product, Category, Brand
from app.schemas.product import ProductCreate, ProductUpdate


async def create_product(session: AsyncSession, data: ProductCreate, created_by_id: Optional[UUID] = None) -> Product:
    """Create a new product master entity."""
    # Verify category exists
    cat_res = await session.execute(select(Category).where(Category.id == data.category_id))
    if not cat_res.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category with id '{data.category_id}' not found.",
        )

    # Check for duplicate SKU
    sku_res = await session.execute(select(Product).where(Product.sku == data.sku, Product.is_deleted == False))
    if sku_res.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Product with SKU '{data.sku}' already exists.",
        )

    # Check for duplicate barcode if provided
    if data.barcode:
        bc_res = await session.execute(select(Product).where(Product.barcode == data.barcode, Product.is_deleted == False))
        if bc_res.scalars().first():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Product with barcode '{data.barcode}' already exists.",
            )

    product = Product(
        name=data.name,
        description=data.description,
        sku=data.sku,
        barcode=data.barcode,
        category_id=data.category_id,
        brand_id=data.brand_id,
        unit_of_measure=data.unit_of_measure,
        unit_price=data.unit_price,
        cost_price=data.cost_price,
        reorder_point=data.reorder_point,
        reorder_quantity=data.reorder_quantity,
        shelf_life_days=data.shelf_life_days,
        has_expiry=data.has_expiry,
        image_url=data.image_url,
        is_active=data.is_active,
        created_by=created_by_id,
    )

    session.add(product)
    await session.commit()

    return await get_product_by_id(session, product.id)


async def get_product_by_id(session: AsyncSession, product_id: UUID) -> Product:
    """Get product by ID with category and brand eager loaded."""
    result = await session.execute(
        select(Product)
        .options(joinedload(Product.category), joinedload(Product.brand))
        .where(Product.id == product_id, Product.is_deleted == False)
    )
    product = result.scalars().first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with id '{product_id}' not found.",
        )
    return product


async def list_products(
    session: AsyncSession,
    skip: int = 0,
    limit: int = 20,
    category_id: Optional[UUID] = None,
    search: Optional[str] = None,
    barcode: Optional[str] = None,
    is_active: Optional[bool] = None,
) -> Tuple[List[Product], int]:
    """List products with pagination, category filter, barcode filter, and text search."""
    stmt = select(Product).options(joinedload(Product.category), joinedload(Product.brand)).where(Product.is_deleted == False)

    if category_id:
        stmt = stmt.where(Product.category_id == category_id)

    if is_active is not None:
        stmt = stmt.where(Product.is_active == is_active)

    if barcode:
        stmt = stmt.where(Product.barcode == barcode)

    if search:
        search_filter = f"%{search}%"
        stmt = stmt.where(Product.name.ilike(search_filter) | Product.sku.ilike(search_filter) | Product.barcode.ilike(search_filter))

    # Total count query
    count_stmt = select(func.count()).select_from(select(Product.id).where(Product.is_deleted == False).subquery())
    total_res = await session.execute(count_stmt)
    total = total_res.scalar() or 0

    # Paginated results
    stmt = stmt.offset(skip).limit(limit)
    result = await session.execute(stmt)
    products = result.scalars().unique().all()

    return products, total


async def update_product(session: AsyncSession, product_id: UUID, data: ProductUpdate) -> Product:
    """Update a product."""
    product = await get_product_by_id(session, product_id)

    update_dict = data.model_dump(exclude_unset=True)

    if "category_id" in update_dict and update_dict["category_id"]:
        cat_res = await session.execute(select(Category).where(Category.id == update_dict["category_id"]))
        if not cat_res.scalars().first():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Category with id '{update_dict['category_id']}' not found.",
            )

    for key, value in update_dict.items():
        setattr(product, key, value)

    await session.commit()
    return await get_product_by_id(session, product_id)


async def deactivate_product(session: AsyncSession, product_id: UUID) -> Product:
    """Soft deactivate a product."""
    product = await get_product_by_id(session, product_id)
    product.is_active = False
    await session.commit()
    return await get_product_by_id(session, product_id)
