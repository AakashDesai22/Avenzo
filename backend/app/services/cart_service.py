"""
AVENZO Backend — Consumer Cart Service
Business logic for managing consumer shopping carts, line items, and stock availability checks.
"""

from typing import Optional
from uuid import UUID
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from fastapi import HTTPException, status

from app.models.cart import Cart, CartItem
from app.models.product import Product
from app.schemas.cart import CartRead, CartItemRead, CartItemAddRequest, CartItemUpdateRequest
from app.services import marketplace_service


async def get_or_create_active_cart(session: AsyncSession, user_id: UUID) -> Cart:
    """Retrieves current user's active cart or creates a new one."""
    stmt = (
        select(Cart)
        .options(
            joinedload(Cart.items).joinedload(CartItem.product).joinedload(Product.category),
            joinedload(Cart.items).joinedload(CartItem.product).joinedload(Product.brand),
        )
        .where(Cart.user_id == user_id, Cart.status == "ACTIVE")
    )
    result = await session.execute(stmt)
    cart = result.scalars().unique().first()

    if not cart:
        cart = Cart(user_id=user_id, status="ACTIVE")
        session.add(cart)
        await session.commit()
        await session.refresh(cart)
        # Re-fetch with options
        result = await session.execute(stmt)
        cart = result.scalars().unique().first()

    return cart


async def build_cart_read_model(session: AsyncSession, cart: Cart) -> CartRead:
    """Builds consumer CartRead payload with calculated totals and live marketplace availability."""
    product_ids = [item.product_id for item in cart.items if item.product and item.product.is_active and not item.product.is_deleted]
    availability_map = await marketplace_service.get_product_availability_map(session, product_ids)

    item_views: list[CartItemRead] = []
    subtotal = Decimal("0.00")
    total_qty = 0

    for item in cart.items:
        prod = item.product
        if not prod or not prod.is_active or prod.is_deleted:
            continue

        avail_qty = availability_map.get(prod.id, 0)
        prod_mkt = marketplace_service.MarketplaceProductRead(
            id=prod.id,
            name=prod.name,
            description=prod.description,
            sku=prod.sku,
            barcode=prod.barcode,
            category_id=prod.category_id,
            category=prod.category,
            brand_id=prod.brand_id,
            brand=prod.brand,
            unit_of_measure=prod.unit_of_measure,
            unit_price=prod.unit_price,
            shelf_life_days=prod.shelf_life_days,
            has_expiry=prod.has_expiry,
            image_url=prod.image_url,
            is_active=prod.is_active,
            available_quantity=avail_qty,
            is_available=avail_qty > 0,
        )

        item_subtotal = Decimal(item.quantity) * (prod.unit_price or Decimal("0.00"))
        subtotal += item_subtotal
        total_qty += item.quantity

        item_views.append(
            CartItemRead(
                id=item.id,
                cart_id=item.cart_id,
                product_id=item.product_id,
                quantity=item.quantity,
                product=prod_mkt,
                created_at=item.created_at,
                updated_at=item.updated_at,
            )
        )

    return CartRead(
        id=cart.id,
        user_id=cart.user_id,
        status=cart.status,
        items=item_views,
        total_items_count=total_qty,
        calculated_subtotal=subtotal,
        created_at=cart.created_at,
        updated_at=cart.updated_at,
    )


async def get_user_cart(session: AsyncSession, user_id: UUID) -> CartRead:
    """Gets active cart for specified consumer user."""
    cart = await get_or_create_active_cart(session, user_id)
    return await build_cart_read_model(session, cart)


async def add_item_to_cart(session: AsyncSession, user_id: UUID, data: CartItemAddRequest) -> CartRead:
    """Adds product item to consumer cart. Increments quantity if product already exists in cart."""
    # Verify product exists and is active
    prod_stmt = select(Product).where(Product.id == data.product_id, Product.is_active == True, Product.is_deleted == False)
    prod_res = await session.execute(prod_stmt)
    prod = prod_res.scalars().first()
    if not prod:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Product with ID '{data.product_id}' is not available for purchase.",
        )

    cart = await get_or_create_active_cart(session, user_id)

    # Check existing item
    existing_item = next((i for i in cart.items if i.product_id == data.product_id), None)
    if existing_item:
        existing_item.quantity += data.quantity
    else:
        new_item = CartItem(cart_id=cart.id, product_id=data.product_id, quantity=data.quantity)
        session.add(new_item)

    await session.commit()
    session.expire(cart, ["items"])
    return await get_user_cart(session, user_id)


async def update_cart_item(session: AsyncSession, user_id: UUID, item_id: UUID, data: CartItemUpdateRequest) -> CartRead:
    """Updates quantity of item in cart. Removes item if quantity is 0."""
    cart = await get_or_create_active_cart(session, user_id)
    target_item = next((i for i in cart.items if i.id == item_id), None)

    if not target_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cart item with ID '{item_id}' not found in active cart.",
        )

    if data.quantity <= 0:
        await session.delete(target_item)
    else:
        target_item.quantity = data.quantity

    await session.commit()
    session.expire(cart, ["items"])
    return await get_user_cart(session, user_id)


async def remove_cart_item(session: AsyncSession, user_id: UUID, item_id: UUID) -> CartRead:
    """Removes a line item from active cart."""
    cart = await get_or_create_active_cart(session, user_id)
    target_item = next((i for i in cart.items if i.id == item_id), None)

    if not target_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cart item with ID '{item_id}' not found in active cart.",
        )

    await session.delete(target_item)
    await session.commit()
    session.expire(cart, ["items"])
    return await get_user_cart(session, user_id)


async def clear_cart(session: AsyncSession, user_id: UUID) -> CartRead:
    """Clears all line items from consumer active cart."""
    cart = await get_or_create_active_cart(session, user_id)
    for item in list(cart.items):
        await session.delete(item)
    await session.commit()
    session.expire(cart, ["items"])
    return await get_user_cart(session, user_id)
