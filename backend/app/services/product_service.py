"""
AVENZO Backend — Product Service
Business logic for managing Product Master catalogue.
"""

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload

from app.models.product import Category, Product
from app.schemas.product import ProductCreate, ProductUpdate


async def create_product(session: AsyncSession, data: ProductCreate, created_by_id: UUID | None = None) -> Product:
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
        is_published=data.is_published,
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
    category_id: UUID | None = None,
    search: str | None = None,
    barcode: str | None = None,
    is_active: bool | None = None,
    is_published: bool | None = None,
) -> tuple[list[Product], int]:
    """List products with pagination, category filter, barcode filter, and text search."""
    # Build shared filter conditions applied to both count and results queries
    base_conditions = [Product.is_deleted == False]

    if category_id:
        base_conditions.append(Product.category_id == category_id)

    if is_active is not None:
        base_conditions.append(Product.is_active == is_active)

    if is_published is not None:
        base_conditions.append(Product.is_published == is_published)

    if barcode:
        base_conditions.append(Product.barcode == barcode)

    if search:
        search_filter = f"%{search}%"
        base_conditions.append(
            Product.name.ilike(search_filter)
            | Product.sku.ilike(search_filter)
            | Product.barcode.ilike(search_filter)
        )

    # Total count with the same filters applied (bug fix: previously ignored filters)
    count_stmt = select(func.count(Product.id)).where(*base_conditions)
    total_res = await session.execute(count_stmt)
    total = total_res.scalar() or 0

    # Paginated results
    stmt = (
        select(Product)
        .options(joinedload(Product.category), joinedload(Product.brand))
        .where(*base_conditions)
        .offset(skip)
        .limit(limit)
    )
    result = await session.execute(stmt)
    products = result.scalars().unique().all()

    return products, total


async def update_product(session: AsyncSession, product_id: UUID, data: ProductUpdate) -> Product:
    """Update a product."""
    product = await get_product_by_id(session, product_id)

    update_dict = data.model_dump(exclude_unset=True)

    if update_dict.get("category_id"):
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
    """Soft deactivate a product. Also unpublishes it to hide from consumer marketplace."""
    product = await get_product_by_id(session, product_id)
    product.is_active = False
    product.is_published = False
    await session.commit()
    return await get_product_by_id(session, product_id)


async def publish_product(
    session: AsyncSession, product_id: UUID, require_stock: bool = False
) -> Product:
    """
    Publish a product to make it visible in the consumer marketplace.
    Validates product is active, non-deleted, category is active, has valid pricing,
    and optionally validates sellable non-expired stock.
    """
    product = await get_product_by_id(session, product_id)

    if not product.is_active or getattr(product, "is_deleted", False):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot publish product '{product.name}': Product is inactive or deleted.",
        )

    if product.category and not product.category.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot publish product '{product.name}': Category '{product.category.name}' is inactive. Please activate the category first.",
        )

    if product.unit_price is None or product.unit_price <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot publish product '{product.name}': Valid unit selling price greater than zero is required.",
        )

    if require_stock:
        from app.services.marketplace_service import get_product_availability_map

        avail_map = await get_product_availability_map(session, [product.id])
        stock = avail_map.get(product.id, 0)
        if stock <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot publish product '{product.name}' for consumer sale: No valid sellable stock available in active, non-expired batches.",
            )

    product.is_published = True
    await session.commit()
    return await get_product_by_id(session, product_id)


async def unpublish_product(session: AsyncSession, product_id: UUID) -> Product:
    """
    Revert a product to draft state, hiding it from the consumer marketplace.
    The product remains in the admin catalogue with all data intact.
    """
    product = await get_product_by_id(session, product_id)
    product.is_published = False
    await session.commit()
    return await get_product_by_id(session, product_id)
