"""
AVENZO Backend — Closed-Loop Waste & Utilization Analytics Pydantic Schemas
"""

from uuid import UUID
from typing import Optional, List, Dict, Any
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field


class CategoryWasteBreakdown(BaseModel):
    category_name: str
    discarded_quantity: float
    percentage_of_total_waste: float


class ConsumerWasteMetricsRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: UUID
    total_items_tracked: int
    total_items_consumed: int
    total_items_discarded: int
    total_items_expired: int
    consumed_quantity: float
    discarded_quantity: float
    expired_quantity: float
    consumption_ratio: float  # e.g., 0.85 for 85%
    waste_ratio: float        # e.g., 0.15 for 15%
    waste_reduction_score: Optional[int] = Field(None, ge=0, le=100) # 0 to 100, None if insufficient history
    estimated_money_saved: float
    has_sufficient_history: bool
    history_status: str
    top_wasted_categories: List[CategoryWasteBreakdown] = []


class SpoilageProductSummary(BaseModel):
    product_id: UUID
    product_name: str
    sku: str
    category_name: str
    discarded_quantity: float
    discard_events_count: int


class BusinessWasteAnalyticsRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    total_warehouse_expired_units: int
    total_capital_lost_expired: float
    total_consumer_reported_discards: float
    total_consumer_reported_consumptions: float
    overall_inventory_waste_percentage: float
    top_spoilage_products: List[SpoilageProductSummary] = []
    has_sufficient_business_data: bool
