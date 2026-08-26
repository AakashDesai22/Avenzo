"""
AVENZO Backend — Consumer Orders API Router (/api/v1/orders)
Provides consumer checkout, order history, and order detail endpoints.
"""

from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Header, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import require_roles
from app.models.user import User
from app.schemas.order import OrderCheckoutRequest, OrderRead
from app.schemas.order_allocation import OrderBatchAllocationRead
from app.schemas.common import ApiResponse
from app.services import checkout_service, fulfillment_service

router = APIRouter(prefix="/orders", tags=["Consumer Orders & Order Fulfillment"])


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


@router.get("", response_model=ApiResponse[List[OrderRead]])
async def list_all_orders_endpoint(
    status_filter: Optional[str] = Query(None, alias="status", description="Optional status filter"),
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["ADMIN", "BUSINESS_MANAGER", "STAFF"])),
):
    """List operational consumer orders across all users (ADMIN, BUSINESS_MANAGER, STAFF)."""
    orders = await fulfillment_service.list_all_orders(session, status_filter=status_filter)
    return ApiResponse(success=True, data=orders)


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


@router.get("/{order_id}", response_model=ApiResponse[OrderRead])
async def get_business_order_detail_endpoint(
    order_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["ADMIN", "BUSINESS_MANAGER", "STAFF"])),
):
    """Get operational order detail view by ID for business roles (ADMIN, BUSINESS_MANAGER, STAFF)."""
    order = await fulfillment_service.get_business_order_by_id(session, order_id)
    return ApiResponse(success=True, data=order)


# ----------------------------------------------------------------------
# PHASE 10C: OPERATIONAL ORDER FULFILLMENT ENDPOINTS
# ----------------------------------------------------------------------

@router.post("/{order_id}/confirm", response_model=ApiResponse[OrderRead])
async def confirm_order_endpoint(
    order_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["ADMIN", "BUSINESS_MANAGER"])),
):
    """Confirm pending order (ADMIN, BUSINESS_MANAGER)."""
    order = await fulfillment_service.confirm_order(session, order_id)
    return ApiResponse(success=True, data=order, message="Order confirmed successfully.")


@router.post("/{order_id}/allocate", response_model=ApiResponse[OrderRead])
async def allocate_order_fefo_endpoint(
    order_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["ADMIN", "BUSINESS_MANAGER"])),
):
    """Execute server-side FEFO batch allocation for confirmed order (ADMIN, BUSINESS_MANAGER)."""
    order = await fulfillment_service.allocate_order_fefo(session, order_id)
    return ApiResponse(success=True, data=order, message="Order FEFO batch allocation complete.")


@router.post("/{order_id}/pack", response_model=ApiResponse[OrderRead])
async def pack_order_endpoint(
    order_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["ADMIN", "BUSINESS_MANAGER"])),
):
    """Mark order as packed and ready for dispatch (ADMIN, BUSINESS_MANAGER)."""
    order = await fulfillment_service.pack_order(session, order_id)
    return ApiResponse(success=True, data=order, message="Order packed successfully.")


@router.post("/{order_id}/dispatch", response_model=ApiResponse[OrderRead])
async def dispatch_order_endpoint(
    order_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["ADMIN", "BUSINESS_MANAGER"])),
):
    """Dispatch/ship packed order and execute physical inventory stock deduction (ADMIN, BUSINESS_MANAGER)."""
    order = await fulfillment_service.dispatch_order(session, order_id)
    return ApiResponse(success=True, data=order, message="Order dispatched/shipped. Physical stock deducted.")


@router.post("/{order_id}/deliver", response_model=ApiResponse[OrderRead])
async def deliver_order_endpoint(
    order_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["ADMIN", "BUSINESS_MANAGER"])),
):
    """Mark shipped order as delivered to consumer (ADMIN, BUSINESS_MANAGER)."""
    order = await fulfillment_service.deliver_order(session, order_id)
    return ApiResponse(success=True, data=order, message="Order delivered successfully.")


@router.post("/{order_id}/cancel", response_model=ApiResponse[OrderRead])
async def cancel_order_endpoint(
    order_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["ADMIN", "BUSINESS_MANAGER", "CONSUMER"])),
):
    """Cancel order pre-shipment and release reserved inventory stock (ADMIN, BUSINESS_MANAGER, CONSUMER for own order)."""
    is_consumer = current_user.role.name == "CONSUMER" if current_user.role else False
    order = await fulfillment_service.cancel_order(
        session, order_id, user_id=current_user.id, is_consumer=is_consumer
    )
    return ApiResponse(success=True, data=order, message="Order cancelled and stock reservation released.")


@router.get("/{order_id}/allocations", response_model=ApiResponse[List[OrderBatchAllocationRead]])
async def get_order_allocations_endpoint(
    order_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["ADMIN", "BUSINESS_MANAGER", "STAFF", "CONSUMER"])),
):
    """Retrieve exact batch allocation details for an order (ADMIN, BUSINESS_MANAGER, STAFF, CONSUMER for own order)."""
    is_consumer = current_user.role.name == "CONSUMER" if current_user.role else False
    allocs = await fulfillment_service.get_order_allocations(
        session, order_id, user_id=current_user.id, is_consumer=is_consumer
    )
    return ApiResponse(success=True, data=allocs)
