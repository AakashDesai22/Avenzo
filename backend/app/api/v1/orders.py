"""
AVENZO Backend — Consumer Orders API Router (/api/v1/orders)
Provides consumer checkout, order history, and order detail endpoints.
"""

from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Header, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import require_roles
from app.models.user import User
from app.schemas.order import OrderCheckoutRequest, OrderRead
from app.schemas.common import ApiResponse
from app.services import checkout_service

router = APIRouter(prefix="/orders", tags=["Consumer Orders & Checkout"])


@router.post("", response_model=ApiResponse[OrderRead], status_code=status.HTTP_201_CREATED)
async def checkout_order(
    data: OrderCheckoutRequest,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["CONSUMER"])),
):
    """
    Checkout active consumer cart into a purchase order.
    Reserves stock and logs inventory transaction audit records.
    Supports Idempotency-Key header for duplicate protection.
    """
    order = await checkout_service.process_checkout(
        session, current_user.id, data, idempotency_key=idempotency_key
    )
    return ApiResponse(
        success=True,
        data=order,
        message="Order placed successfully.",
    )


@router.get("/my", response_model=ApiResponse[List[OrderRead]])
async def list_my_orders(
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["CONSUMER"])),
):
    """List order history for current consumer user."""
    orders = await checkout_service.list_user_orders(session, current_user.id)
    return ApiResponse(success=True, data=orders)


@router.get("/my/{order_id}", response_model=ApiResponse[OrderRead])
async def get_my_order_detail(
    order_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["CONSUMER"])),
):
    """Get detailed consumer order view by ID."""
    order = await checkout_service.get_order_by_id(session, order_id, current_user.id)
    return ApiResponse(success=True, data=order)
