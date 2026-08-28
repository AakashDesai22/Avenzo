"""
AVENZO Backend — Closed-Loop Waste & Utilization Analytics Service
Derives consumer waste reduction metrics and aggregate privacy-safe business analytics
directly from authoritative database models (PantryItemLog, PantryItem, Inventory, Batch, Product).
"""

from uuid import UUID
from typing import List, Dict, Any, Optional
from datetime import date
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, and_, or_
from sqlalchemy.orm import selectinload, joinedload

from app.models.pantry import ConsumerPantry, PantryItem, PantryItemLog
from app.models.product import Product, Category
from app.models.inventory import Inventory, Batch
from app.models.order import OrderItem
from app.schemas.analytics import (
    ConsumerWasteMetricsRead,
    CategoryWasteBreakdown,
    BusinessWasteAnalyticsRead,
    SpoilageProductSummary,
)


async def get_consumer_waste_analytics(
    session: AsyncSession, user_id: UUID
) -> ConsumerWasteMetricsRead:
    """
    Computes deterministic consumer utilization and waste reduction analytics
    based on PantryItemLog audit records and PantryItem status.
    """
    # 1. Fetch user pantries
    pantry_stmt = select(ConsumerPantry.id).where(ConsumerPantry.user_id == user_id)
    pantry_res = await session.execute(pantry_stmt)
    pantry_ids = pantry_res.scalars().all()

    if not pantry_ids:
        return ConsumerWasteMetricsRead(
            user_id=user_id,
            total_items_tracked=0,
            total_items_consumed=0,
            total_items_discarded=0,
            total_items_expired=0,
            consumed_quantity=0.0,
            discarded_quantity=0.0,
            expired_quantity=0.0,
            consumption_ratio=0.0,
            waste_ratio=0.0,
            waste_reduction_score=None,
            estimated_money_saved=0.0,
            has_sufficient_history=False,
            history_status="No pantry activity logged yet. Add items to track waste reduction.",
            top_wasted_categories=[],
        )

    # 2. Fetch all pantry items belonging to user with products, categories, order items, and logs
    items_stmt = (
        select(PantryItem)
        .options(
            joinedload(PantryItem.product).joinedload(Product.category),
            joinedload(PantryItem.order_item),
            selectinload(PantryItem.logs),
        )
        .where(
            PantryItem.pantry_id.in_(pantry_ids),
            PantryItem.is_deleted == False,
        )
    )
    items_res = await session.execute(items_stmt)
    items = items_res.scalars().unique().all()

    total_items_tracked = len(items)
    items_consumed_count = sum(1 for i in items if i.status == "consumed")
    items_discarded_count = sum(1 for i in items if i.status == "discarded")
    items_expired_count = sum(1 for i in items if i.status == "expired")

    consumed_qty = Decimal("0.0")
    discarded_qty = Decimal("0.0")
    expired_qty = Decimal("0.0")
    estimated_savings = Decimal("0.0")

    category_waste_map: Dict[str, Decimal] = {}

    for item in items:
        # Determine price snapshot for money saved calculation
        unit_price = Decimal("0.0")
        if item.order_item and item.order_item.unit_price is not None:
            unit_price = Decimal(str(item.order_item.unit_price))
        elif item.product and item.product.unit_price is not None:
            unit_price = Decimal(str(item.product.unit_price))

        cat_name = item.product.category.name if (item.product and item.product.category) else "General Pantry"

        for log in item.logs:
            if log.action == "CONSUMED":
                qty = abs(Decimal(str(log.quantity_change)))
                consumed_qty += qty
                estimated_savings += qty * unit_price
            elif log.action == "DISCARDED":
                qty = abs(Decimal(str(log.quantity_change)))
                discarded_qty += qty
                category_waste_map[cat_name] = category_waste_map.get(cat_name, Decimal("0.0")) + qty
            elif log.action == "EXPIRED_REMOVED":
                qty = abs(Decimal(str(log.quantity_change)))
                expired_qty += qty
                category_waste_map[cat_name] = category_waste_map.get(cat_name, Decimal("0.0")) + qty

        # If item status is discarded or expired without explicit log entry
        if item.status == "discarded" and not any(l.action == "DISCARDED" for l in item.logs):
            qty = Decimal(str(item.quantity))
            discarded_qty += qty
            category_waste_map[cat_name] = category_waste_map.get(cat_name, Decimal("0.0")) + qty
        elif item.status == "expired" and not any(l.action == "EXPIRED_REMOVED" for l in item.logs):
            qty = Decimal(str(item.quantity))
            expired_qty += qty
            category_waste_map[cat_name] = category_waste_map.get(cat_name, Decimal("0.0")) + qty

    total_activity_qty = consumed_qty + discarded_qty + expired_qty
    total_logs_count = sum(len(i.logs) for i in items)

    # Insufficient history check: requires at least 3 items tracked or >= 2 logged actions
    has_sufficient_history = (total_items_tracked >= 3) or (total_logs_count >= 2 and total_activity_qty > Decimal("0"))

    if not has_sufficient_history or total_activity_qty == Decimal("0"):
        consumption_ratio = 0.0
        waste_ratio = 0.0
        waste_reduction_score = None
        history_status = "Track more pantry activity to unlock your Waste Reduction Index."
    else:
        c_ratio = consumed_qty / total_activity_qty
        w_ratio = (discarded_qty + expired_qty) / total_activity_qty
        consumption_ratio = round(float(c_ratio), 4)
        waste_ratio = round(float(w_ratio), 4)
        # Deterministic 0 - 100 Score = Consumption Ratio * 100
        waste_reduction_score = int(round(float(c_ratio) * 100))
        waste_reduction_score = max(0, min(100, waste_reduction_score))
        history_status = "Active pantry waste tracking"

    # Format top wasted categories
    top_categories: List[CategoryWasteBreakdown] = []
    total_wasted_qty = discarded_qty + expired_qty
    if total_wasted_qty > Decimal("0"):
        sorted_cats = sorted(category_waste_map.items(), key=lambda x: x[1], reverse=True)[:5]
        for c_name, w_qty in sorted_cats:
            pct = float((w_qty / total_wasted_qty) * Decimal("100.0"))
            top_categories.append(
                CategoryWasteBreakdown(
                    category_name=c_name,
                    discarded_quantity=round(float(w_qty), 2),
                    percentage_of_total_waste=round(pct, 1),
                )
            )

    return ConsumerWasteMetricsRead(
        user_id=user_id,
        total_items_tracked=total_items_tracked,
        total_items_consumed=items_consumed_count,
        total_items_discarded=items_discarded_count,
        total_items_expired=items_expired_count,
        consumed_quantity=round(float(consumed_qty), 2),
        discarded_quantity=round(float(discarded_qty), 2),
        expired_quantity=round(float(expired_qty), 2),
        consumption_ratio=consumption_ratio,
        waste_ratio=waste_ratio,
        waste_reduction_score=waste_reduction_score,
        estimated_money_saved=round(float(estimated_savings), 2),
        has_sufficient_history=has_sufficient_history,
        history_status=history_status,
        top_wasted_categories=top_categories,
    )


async def get_business_waste_analytics(session: AsyncSession) -> BusinessWasteAnalyticsRead:
    """
    Computes privacy-safe aggregate business inventory waste analytics.
    Excludes all consumer personal identifying data.
    """
    # 1. Calculate Warehouse Expired Stock & Capital Exposure
    inv_stmt = (
        select(Inventory)
        .options(
            joinedload(Inventory.batch),
            joinedload(Inventory.product),
        )
        .join(Batch, Inventory.batch_id == Batch.id)
    )
    inv_res = await session.execute(inv_stmt)
    inventories = inv_res.scalars().unique().all()

    total_stock_units = 0
    expired_warehouse_units = 0
    capital_lost_expired = Decimal("0.0")

    for inv in inventories:
        qty = inv.quantity_on_hand or 0
        total_stock_units += qty

        # Check if batch status is expired or DTE < 0
        is_expired = False
        if inv.batch:
            if inv.batch.status == "expired":
                is_expired = True
            elif inv.batch.expiry_date:
                today = date.today()
                if inv.batch.expiry_date < today:
                    is_expired = True

        if is_expired:
            expired_warehouse_units += qty
            cost = Decimal(str(inv.product.cost_price)) if (inv.product and inv.product.cost_price) else Decimal("0.0")
            capital_lost_expired += Decimal(str(qty)) * cost

    overall_waste_pct = 0.0
    if total_stock_units > 0:
        overall_waste_pct = round((expired_warehouse_units / total_stock_units) * 100.0, 1)

    # 2. Compute Consumer-Reported Discard and Consumption Aggregates across platform
    log_stmt = (
        select(
            PantryItemLog.action,
            func.sum(func.abs(PantryItemLog.quantity_change)).label("total_qty"),
        )
        .where(PantryItemLog.action.in_(["CONSUMED", "DISCARDED", "EXPIRED_REMOVED"]))
        .group_by(PantryItemLog.action)
    )
    log_res = await session.execute(log_stmt)
    log_summary = {row.action: float(row.total_qty or 0) for row in log_res.all()}

    total_consumer_consumptions = log_summary.get("CONSUMED", 0.0)
    total_consumer_discards = log_summary.get("DISCARDED", 0.0) + log_summary.get("EXPIRED_REMOVED", 0.0)

    # 3. Top Spoilage Products (Product-level aggregate discard count)
    spoilage_stmt = (
        select(
            Product.id.label("product_id"),
            Product.name.label("product_name"),
            Product.sku.label("sku"),
            Category.name.label("category_name"),
            func.sum(func.abs(PantryItemLog.quantity_change)).label("discarded_qty"),
            func.count(PantryItemLog.id).label("events_count"),
        )
        .select_from(PantryItemLog)
        .join(PantryItem, PantryItemLog.pantry_item_id == PantryItem.id)
        .join(Product, PantryItem.product_id == Product.id)
        .outerjoin(Category, Product.category_id == Category.id)
        .where(PantryItemLog.action.in_(["DISCARDED", "EXPIRED_REMOVED"]))
        .group_by(Product.id, Product.name, Product.sku, Category.name)
        .order_by(func.sum(func.abs(PantryItemLog.quantity_change)).desc())
        .limit(5)
    )
    spoilage_res = await session.execute(spoilage_stmt)
    spoilage_rows = spoilage_res.all()

    top_spoilage: List[SpoilageProductSummary] = [
        SpoilageProductSummary(
            product_id=row.product_id,
            product_name=row.product_name,
            sku=row.sku,
            category_name=row.category_name or "General",
            discarded_quantity=round(float(row.discarded_qty), 2),
            discard_events_count=row.events_count,
        )
        for row in spoilage_rows
    ]

    has_data = total_stock_units > 0 or total_consumer_discards > 0 or total_consumer_consumptions > 0

    return BusinessWasteAnalyticsRead(
        total_warehouse_expired_units=expired_warehouse_units,
        total_capital_lost_expired=round(float(capital_lost_expired), 2),
        total_consumer_reported_discards=round(total_consumer_discards, 2),
        total_consumer_reported_consumptions=round(total_consumer_consumptions, 2),
        overall_inventory_waste_percentage=overall_waste_pct,
        top_spoilage_products=top_spoilage,
        has_sufficient_business_data=has_data,
    )
