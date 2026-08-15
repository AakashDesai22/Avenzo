"""
AVENZO Backend — Expiry Intelligence and Inventory Risk Schemas
"""

from uuid import UUID
from typing import Optional
from decimal import Decimal
from pydantic import BaseModel, ConfigDict


class ExpirySummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    warehouse_id: Optional[UUID] = None
    category_id: Optional[UUID] = None
    total_items_tracked: int
    safe_quantity: int
    expiring_soon_quantity: int
    critical_quantity: int
    expired_quantity: int
    non_expiry_quantity: int
    safe_batches_count: int
    expiring_soon_batches_count: int
    critical_batches_count: int
    expired_batches_count: int


class InventoryRiskMetricsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    warehouse_id: Optional[UUID] = None
    total_stock_quantity: int
    near_expiry_quantity: int  # DTE <= 30 days
    critical_expiry_quantity: int  # DTE <= 7 days
    expired_quantity: int  # DTE < 0
    expiry_exposure_percentage: float  # ((near_expiry + expired) / total) * 100
    capital_exposure_at_risk: Decimal  # sum(quantity * product.cost_price) for near-expiry + expired
    potential_sales_exposure: Decimal  # sum(quantity * product.unit_price) for near-expiry + expired
