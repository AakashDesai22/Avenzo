"""
AVENZO Backend — Consumer Marketplace Service
Server-side business logic for consumer product catalog, availability calculation,
and non-expired sellable inventory aggregation across valid batches.
"""

from typing import List, Tuple, Optional
from uuid import UUID
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, or_, and_, case
from sqlalchemy.orm import joinedload

from app.core.date_utils import get_business_date
from app.models.product import Product
from app.models.inventory import Inventory, Batch
from app.schemas.marketplace import MarketplaceProductRead


async def get_product_availability_map(
    session: AsyncSession, product_ids: List[UUID], target_date: Optional[date] = None
) -> dict[UUID, int]:
    """
    Calculates aggregated available stock (quantity_on_hand - quantity_reserved)
    across all active, non-expired batches for a list of product IDs in a single query.
    Uses ANSI SQL CASE syntax compatible with both PostgreSQL and SQLite.
    """
    if not product_ids:
        return {}

    ref_date = target_date or get_business_date()

    # Calculate net available quantity per inventory record (on_hand - reserved)
    net_avail = Inventory.quantity_on_hand - Inventory.quantity_reserved

    # Condition for valid sellable stock: batch active, and (no expiry OR expiry_date > ref_date)
    valid_batch_cond = and_(
        Batch.status == "active",
        net_avail > 0,
        or_(
            Product.has_expiry == False,
            Batch.expiry_date == None,
            Batch.expiry_date > ref_date,
        ),
    )

    # Filtered available stock sum using ANSI SQL case statement
    sellable_stock_expr = func.coalesce(
        func.sum(
            case(
                (valid_batch_cond, net_avail),
                else_=0,
            )
        ),
        0,
    )

    stmt = (
        select(Product.id, sellable_stock_expr.label("available_qty"))
        .outerjoin(Inventory, Inventory.product_id == Product.id)
        .outerjoin(Batch, Inventory.batch_id == Batch.id)
        .where(Product.id.in_(product_ids))
        .group_by(Product.id)
    )

    result = await session.execute(stmt)
    return {row.id: int(row.available_qty) for row in result.all()}


async def list_marketplace_products(
    session: AsyncSession,
    skip: int = 0,
    limit: int = 20,
    category_id: Optional[UUID] = None,
    search: Optional[str] = None,
    in_stock_only: bool = False,
) -> Tuple[List[MarketplaceProductRead], int]:
    """
    Lists consumer-facing marketplace products with aggregated available stock.
    Avoids N+1 query patterns by fetching product batch availability in a single SQL operation.
    """
    business_date = get_business_date()

    # Base filter conditions for active, non-deleted products
    filters = [Product.is_active == True, Product.is_deleted == False]

    if category_id:
        filters.append(Product.category_id == category_id)

    if search:
        search_pattern = f"%{search}%"
        filters.append(
            or_(
                Product.name.ilike(search_pattern),
                Product.sku.ilike(search_pattern),
                Product.description.ilike(search_pattern),
            )
        )

    # Count total matching products cleanly without subquery/joinedload option pollution
    count_stmt = select(func.count(Product.id)).where(*filters)
    total_result = await session.execute(count_stmt)
    total = total_result.scalar_one()

    # Execute main product fetch with eager joined relationships
    stmt = (
        select(Product)
        .options(
            joinedload(Product.category),
            joinedload(Product.brand),
        )
        .where(*filters)
        .order_by(Product.name.asc())
        .offset(skip)
        .limit(limit)
    )
    result = await session.execute(stmt)
    products = result.scalars().unique().all()

    if not products:
        return [], total

    # Fetch availability map for all returned product IDs in one single SQL query
    product_ids = [p.id for p in products]
    availability_map = await get_product_availability_map(session, product_ids, target_date=business_date)

    marketplace_items: List[MarketplaceProductRead] = []
    for p in products:
        qty = availability_map.get(p.id, 0)
        if in_stock_only and qty <= 0:
            continue

        item = MarketplaceProductRead(
            id=p.id,
            name=p.name,
            description=p.description,
            sku=p.sku,
            barcode=p.barcode,
            category_id=p.category_id,
            category=p.category,
            brand_id=p.brand_id,
            brand=p.brand,
            unit_of_measure=p.unit_of_measure,
            unit_price=p.unit_price,
            shelf_life_days=p.shelf_life_days,
            has_expiry=p.has_expiry,
            image_url=p.image_url,
            is_active=p.is_active,
            available_quantity=qty,
            is_available=qty > 0,
        )
        marketplace_items.append(item)

    return marketplace_items, total


async def get_marketplace_product_by_id(
    session: AsyncSession, product_id: UUID
) -> Optional[MarketplaceProductRead]:
    """
    Gets detailed consumer marketplace product information including sellable stock.
    Returns None if product is inactive, deleted, or non-existent.
    """
    business_date = get_business_date()

    stmt = (
        select(Product)
        .options(
            joinedload(Product.category),
            joinedload(Product.brand),
        )
        .where(Product.id == product_id, Product.is_active == True, Product.is_deleted == False)
    )

    result = await session.execute(stmt)
    product = result.scalars().first()

    if not product:
        return None

    availability_map = await get_product_availability_map(session, [product.id], target_date=business_date)
    qty = availability_map.get(product.id, 0)

    return MarketplaceProductRead(
        id=product.id,
        name=product.name,
        description=product.description,
        sku=product.sku,
        barcode=product.barcode,
        category_id=product.category_id,
        category=product.category,
        brand_id=product.brand_id,
        brand=product.brand,
        unit_of_measure=product.unit_of_measure,
        unit_price=product.unit_price,
        shelf_life_days=product.shelf_life_days,
        has_expiry=product.has_expiry,
        image_url=product.image_url,
        is_active=product.is_active,
        available_quantity=qty,
        is_available=qty > 0,
    )
