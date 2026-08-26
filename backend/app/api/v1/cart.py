"""
AVENZO Backend — Consumer Cart API Router (/api/v1/cart)
Allows consumers to manage active shopping carts and line items.
"""

from uuid import UUID
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import require_roles
from app.models.user import User
from app.schemas.cart import CartRead, CartItemAddRequest, CartItemUpdateRequest
from app.schemas.common import ApiResponse
from app.services import cart_service

router = APIRouter(prefix="/cart", tags=["Consumer Shopping Cart"])


@router.get("", response_model=ApiResponse[CartRead])
async def get_cart(
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["CONSUMER"])),
):
    """Get active consumer shopping cart."""
    cart = await cart_service.get_user_cart(session, current_user.id)
    return ApiResponse(success=True, data=cart)


@router.post("/items", response_model=ApiResponse[CartRead], status_code=status.HTTP_201_CREATED)
async def add_cart_item(
    data: CartItemAddRequest,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["CONSUMER"])),
):
    """Add product item to active shopping cart."""
    cart = await cart_service.add_item_to_cart(session, current_user.id, data)
    return ApiResponse(success=True, data=cart, message="Item added to cart.")


@router.put("/items/{item_id}", response_model=ApiResponse[CartRead])
async def update_cart_item(
    item_id: UUID,
    data: CartItemUpdateRequest,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["CONSUMER"])),
):
    """Update line item quantity in active shopping cart."""
    cart = await cart_service.update_cart_item(session, current_user.id, item_id, data)
    return ApiResponse(success=True, data=cart, message="Cart item updated.")


@router.delete("/items/{item_id}", response_model=ApiResponse[CartRead])
async def remove_cart_item(
    item_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["CONSUMER"])),
):
    """Remove line item from active shopping cart."""
    cart = await cart_service.remove_cart_item(session, current_user.id, item_id)
    return ApiResponse(success=True, data=cart, message="Cart item removed.")


@router.delete("", response_model=ApiResponse[CartRead])
async def clear_cart(
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["CONSUMER"])),
):
    """Clear all items from active shopping cart."""
    cart = await cart_service.clear_cart(session, current_user.id)
    return ApiResponse(success=True, data=cart, message="Cart cleared.")
