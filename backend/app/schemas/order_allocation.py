"""
AVENZO Backend — Order Batch Allocation Pydantic Schemas
"""

from uuid import UUID
from datetime import datetime, date
from typing import Optional
from pydantic import BaseModel, ConfigDict


class OrderBatchAllocationRead(BaseModel):
    """Consumer/Business view of exact FEFO batch allocation for an OrderItem."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    order_item_id: UUID
    order_id: UUID
    product_id: UUID
    batch_id: UUID
    inventory_id: UUID
    allocated_quantity: int
    batch_number: Optional[str] = None
    expiry_date: Optional[date] = None
    created_at: datetime
    updated_at: datetime
