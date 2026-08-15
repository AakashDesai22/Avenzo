"""
AVENZO Backend — Expiry Intelligence Service
Business logic for Days-To-Expiry (DTE) calculations, status classification,
expiry summaries, and deterministic financial risk metrics.
"""

from typing import Optional, List
from uuid import UUID
from datetime import date
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload

from app.core.config import settings
from app.core.date_utils import get_business_date
from app.models.inventory import Inventory, Batch
from app.models.product import Product
from app.schemas.expiry import ExpirySummaryResponse, InventoryRiskMetricsResponse


def calculate_dte(expiry_date: Optional[date], target_date: Optional[date] = None) -> Optional[int]:
    """Calculates Days Until Expiry (DTE) relative to the given or business date."""
    if not expiry_date:
        return None
    ref_date = target_date or get_business_date()
    return (expiry_date - ref_date).days


def classify_expiry_status(expiry_date: Optional[date], has_expiry: bool = True, target_date: Optional[date] = None) -> str:
    """
    Classifies batch/stock expiry status into SAFE, EXPIRING_SOON, CRITICAL, EXPIRED, or N/A.
    Products with has_expiry == False or no expiry_date MUST return 'N/A'.
    """
    if not has_expiry or not expiry_date:
        return "N/A"

    dte = calculate_dte(expiry_date, target_date=target_date)
    if dte is None:
        return "N/A"

    if dte > settings.EXPIRING_SOON_THRESHOLD_DAYS:
        return "SAFE"
    elif dte > settings.CRITICAL_THRESHOLD_DAYS:
        return "EXPIRING_SOON"
    elif dte >= 0:
        return "CRITICAL"
    else:
        return "EXPIRED"


async def get_expiry_summary(
    session: AsyncSession, warehouse_id: Optional[UUID] = None, category_id: Optional[UUID] = None
) -> ExpirySummaryResponse:
    """
    Aggregates inventory stock by expiry classification status.
    """
    business_date = get_business_date()

    stmt = select(Inventory).options(
        joinedload(Inventory.product),
        joinedload(Inventory.batch),
    )

    if warehouse_id:
        stmt = stmt.where(Inventory.warehouse_id == warehouse_id)

    result = await session.execute(stmt)
    inventories = result.scalars().unique().all()

    if category_id:
        inventories = [inv for inv in inventories if inv.product and inv.product.category_id == category_id]

    total_items = 0
    safe_qty = 0
    exp_soon_qty = 0
    critical_qty = 0
    expired_qty = 0
    non_expiry_qty = 0

    safe_batches = set()
    exp_soon_batches = set()
    critical_batches = set()
    expired_batches = set()

    for inv in inventories:
        qty = inv.quantity_on_hand
        total_items += qty

        if not inv.product or not inv.product.has_expiry or not inv.batch or not inv.batch.expiry_date:
            non_expiry_qty += qty
            continue

        status = classify_expiry_status(inv.batch.expiry_date, has_expiry=True, target_date=business_date)
        batch_id = inv.batch_id

        if status == "SAFE":
            safe_qty += qty
            safe_batches.add(batch_id)
        elif status == "EXPIRING_SOON":
            exp_soon_qty += qty
            exp_soon_batches.add(batch_id)
        elif status == "CRITICAL":
            critical_qty += qty
            critical_batches.add(batch_id)
        elif status == "EXPIRED":
            expired_qty += qty
            expired_batches.add(batch_id)

    return ExpirySummaryResponse(
        warehouse_id=warehouse_id,
        category_id=category_id,
        total_items_tracked=total_items,
        safe_quantity=safe_qty,
        expiring_soon_quantity=exp_soon_qty,
        critical_quantity=critical_qty,
        expired_quantity=expired_qty,
        non_expiry_quantity=non_expiry_qty,
        safe_batches_count=len(safe_batches),
        expiring_soon_batches_count=len(exp_soon_batches),
        critical_batches_count=len(critical_batches),
        expired_batches_count=len(expired_batches),
    )


async def get_risk_metrics(
    session: AsyncSession, warehouse_id: Optional[UUID] = None
) -> InventoryRiskMetricsResponse:
    """
    Calculates deterministic inventory risk metrics and financial capital exposure.
    Capital Exposure at Risk = sum(quantity * product.cost_price) for DTE <= 30 days.
    Potential Sales Exposure = sum(quantity * product.unit_price) for DTE <= 30 days.
    """
    business_date = get_business_date()

    stmt = select(Inventory).options(
        joinedload(Inventory.product),
        joinedload(Inventory.batch),
    )

    if warehouse_id:
        stmt = stmt.where(Inventory.warehouse_id == warehouse_id)

    result = await session.execute(stmt)
    inventories = result.scalars().unique().all()

    total_qty = 0
    near_expiry_qty = 0
    critical_qty = 0
    expired_qty = 0
    capital_at_risk = Decimal("0.00")
    sales_at_risk = Decimal("0.00")

    for inv in inventories:
        qty = inv.quantity_on_hand
        total_qty += qty

        if not inv.product or not inv.product.has_expiry or not inv.batch or not inv.batch.expiry_date:
            continue

        dte = calculate_dte(inv.batch.expiry_date, target_date=business_date)
        if dte is None:
            continue

        cost = inv.product.cost_price or Decimal("0.00")
        price = inv.product.unit_price or Decimal("0.00")

        if dte < 0:
            expired_qty += qty
            capital_at_risk += Decimal(qty) * cost
            sales_at_risk += Decimal(qty) * price
        elif dte <= settings.EXPIRING_SOON_THRESHOLD_DAYS:
            near_expiry_qty += qty
            if dte <= settings.CRITICAL_THRESHOLD_DAYS:
                critical_qty += qty
            capital_at_risk += Decimal(qty) * cost
            sales_at_risk += Decimal(qty) * price

    exposure_pct = round(((near_expiry_qty + expired_qty) / total_qty * 100.0), 2) if total_qty > 0 else 0.0

    return InventoryRiskMetricsResponse(
        warehouse_id=warehouse_id,
        total_stock_quantity=total_qty,
        near_expiry_quantity=near_expiry_qty,
        critical_expiry_quantity=critical_qty,
        expired_quantity=expired_qty,
        expiry_exposure_percentage=exposure_pct,
        capital_exposure_at_risk=capital_at_risk,
        potential_sales_exposure=sales_at_risk,
    )
