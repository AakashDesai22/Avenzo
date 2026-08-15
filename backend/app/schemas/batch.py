"""
AVENZO Backend — Batch Pydantic Schemas
"""

from uuid import UUID
from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, model_validator
from app.schemas.product import ProductRead
from app.schemas.supplier import SupplierRead


class BatchCreate(BaseModel):
    product_id: UUID
    batch_number: str = Field(..., max_length=100)
    manufacturing_date: Optional[date] = None
    expiry_date: Optional[date] = None
    supplier_id: Optional[UUID] = None
    initial_quantity: int = Field(default=0, ge=0)
    status: str = Field(default="active", pattern="^(active|expired|depleted|recalled)$")
    notes: Optional[str] = None

    @model_validator(mode="after")
    def validate_dates(self):
        if self.manufacturing_date and self.expiry_date:
            if self.expiry_date < self.manufacturing_date:
                raise ValueError("Expiry date cannot precede manufacturing date")
        return self


class BatchUpdate(BaseModel):
    manufacturing_date: Optional[date] = None
    expiry_date: Optional[date] = None
    status: Optional[str] = Field(None, pattern="^(active|expired|depleted|recalled)$")
    notes: Optional[str] = None

    @model_validator(mode="after")
    def validate_dates(self):
        if self.manufacturing_date and self.expiry_date:
            if self.expiry_date < self.manufacturing_date:
                raise ValueError("Expiry date cannot precede manufacturing date")
        return self


class BatchRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    product_id: UUID
    product: Optional[ProductRead] = None
    batch_number: str
    manufacturing_date: Optional[date] = None
    expiry_date: Optional[date] = None
    supplier_id: Optional[UUID] = None
    supplier: Optional[SupplierRead] = None
    initial_quantity: int
    status: str
    notes: Optional[str] = None
    created_by: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime
