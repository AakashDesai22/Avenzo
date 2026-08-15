"""
AVENZO Backend — Warehouse & Location Pydantic Schemas
"""

from uuid import UUID
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field


class WarehouseLocationCreate(BaseModel):
    location_code: str = Field(..., max_length=50)
    description: Optional[str] = None
    is_active: bool = True


class WarehouseLocationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    warehouse_id: UUID
    location_code: str
    description: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class WarehouseCreate(BaseModel):
    name: str = Field(..., max_length=150)
    address: Optional[str] = None
    city: Optional[str] = Field(None, max_length=100)
    is_active: bool = True


class WarehouseUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=150)
    address: Optional[str] = None
    city: Optional[str] = Field(None, max_length=100)
    is_active: Optional[bool] = None


class WarehouseRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    address: Optional[str] = None
    city: Optional[str] = None
    is_active: bool
    locations: List[WarehouseLocationRead] = []
    created_at: datetime
    updated_at: datetime
