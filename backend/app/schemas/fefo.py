"""
AVENZO Backend — FEFO (First-Expired, First-Out) Pydantic Schemas
"""

from uuid import UUID
from datetime import date
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field


class FEFORankedBatchRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    batch_id: UUID
    batch_number: str
    product_id: UUID
    product_name: str
    sku: str
    has_expiry: bool
    manufacturing_date: Optional[date] = None
    expiry_date: Optional[date] = None
    days_to_expiry: Optional[int] = None
    expiry_status: str # SAFE, EXPIRING_SOON, CRITICAL, EXPIRED, N/A
    quantity_on_hand: int
    quantity_reserved: int
    quantity_available: int
    warehouse_id: UUID
    warehouse_name: str
    location_id: Optional[UUID] = None
    location_code: Optional[str] = None
    fefo_rank: int


class FEFOAllocationRequest(BaseModel):
    product_id: UUID
    requested_quantity: int = Field(..., gt=0, description="Quantity of units requested for picking")
    warehouse_id: Optional[UUID] = None


class FEFOBatchAllocationItem(BaseModel):
    batch_id: UUID
    batch_number: str
    manufacturing_date: Optional[date] = None
    expiry_date: Optional[date] = None
    days_to_expiry: Optional[int] = None
    expiry_status: str
    allocated_quantity: int
    quantity_available: int
    warehouse_id: UUID
    warehouse_name: str
    location_id: Optional[UUID] = None
    location_code: Optional[str] = None
    fefo_rank: int


class FEFOAllocationPlanResponse(BaseModel):
    product_id: UUID
    product_name: str
    sku: str
    requested_quantity: int
    allocated_total: int
    remaining_unallocated: int
    is_fully_allocated: bool
    allocations: List[FEFOBatchAllocationItem]


class FEFOVerificationRequest(BaseModel):
    product_id: UUID
    selected_batch_id: UUID
    requested_quantity: int = Field(..., gt=0)
    warehouse_id: Optional[UUID] = None
    override_reason: Optional[str] = Field(None, max_length=500)


class FEFOVerificationResponse(BaseModel):
    is_compliant: bool
    violation_detected: bool
    warning_message: Optional[str] = None
    selected_batch_id: UUID
    selected_expiry_date: Optional[date] = None
    earlier_available_batch_id: Optional[UUID] = None
    earlier_available_expiry_date: Optional[date] = None
    bypassed_earlier_quantity: int = 0
    audit_logged: bool = False
