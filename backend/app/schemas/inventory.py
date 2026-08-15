"""
AVENZO Backend — Inventory & Inventory Transaction Pydantic Schemas
"""

from uuid import UUID
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.product import ProductRead
from app.schemas.batch import BatchRead
from app.schemas.warehouse import WarehouseRead, WarehouseLocationRead


class InventoryAdjustRequest(BaseModel):
    product_id: UUID
    batch_id: UUID
    warehouse_id: UUID
    location_id: Optional[UUID] = None
    quantity_change: int = Field(..., description="Positive for addition, negative for reduction")
    transaction_type: str = Field(default="ADJUSTMENT", pattern="^(RECEIPT|ADJUSTMENT|TRANSFER|RESERVATION|RELEASE|SALE|DAMAGE|EXPIRY)$")
    notes: Optional[str] = None


class InventoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    product_id: UUID
    product: Optional[ProductRead] = None
    batch_id: UUID
    batch: Optional[BatchRead] = None
    warehouse_id: UUID
    warehouse: Optional[WarehouseRead] = None
    location_id: Optional[UUID] = None
    location: Optional[WarehouseLocationRead] = None
    quantity_on_hand: int
    quantity_reserved: int
    quantity_available: int
    created_at: datetime
    updated_at: datetime


class InventoryTransactionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    inventory_id: UUID
    transaction_type: str
    quantity_change: int
    quantity_before: int
    quantity_after: int
    reference_id: Optional[UUID] = None
    reference_type: Optional[str] = None
    notes: Optional[str] = None
    performed_by: Optional[UUID] = None
    created_at: datetime
