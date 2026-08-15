"""
AVENZO Backend — Product & Brand Pydantic Schemas
"""

from uuid import UUID
from datetime import datetime
from typing import Optional
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.category import CategoryRead


class BrandRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: Optional[str] = None
    logo_url: Optional[str] = None


class ProductCreate(BaseModel):
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    sku: str = Field(..., max_length=100)
    barcode: Optional[str] = Field(None, max_length=100)
    category_id: UUID
    brand_id: Optional[UUID] = None
    unit_of_measure: str = Field(default="units", max_length=50)
    unit_price: Decimal = Field(..., ge=0)
    cost_price: Optional[Decimal] = Field(None, ge=0)
    reorder_point: Optional[int] = Field(None, ge=0)
    reorder_quantity: Optional[int] = Field(None, ge=0)
    shelf_life_days: Optional[int] = Field(None, ge=0)
    has_expiry: bool = True
    image_url: Optional[str] = Field(None, max_length=500)
    is_active: bool = True


class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    sku: Optional[str] = Field(None, max_length=100)
    barcode: Optional[str] = Field(None, max_length=100)
    category_id: Optional[UUID] = None
    brand_id: Optional[UUID] = None
    unit_of_measure: Optional[str] = Field(None, max_length=50)
    unit_price: Optional[Decimal] = Field(None, ge=0)
    cost_price: Optional[Decimal] = Field(None, ge=0)
    reorder_point: Optional[int] = Field(None, ge=0)
    reorder_quantity: Optional[int] = Field(None, ge=0)
    shelf_life_days: Optional[int] = Field(None, ge=0)
    has_expiry: Optional[bool] = None
    image_url: Optional[str] = Field(None, max_length=500)
    is_active: Optional[bool] = None


class ProductRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: Optional[str] = None
    sku: str
    barcode: Optional[str] = None
    category_id: UUID
    category: Optional[CategoryRead] = None
    brand_id: Optional[UUID] = None
    brand: Optional[BrandRead] = None
    unit_of_measure: str
    unit_price: Decimal
    cost_price: Optional[Decimal] = None
    reorder_point: Optional[int] = None
    reorder_quantity: Optional[int] = None
    shelf_life_days: Optional[int] = None
    has_expiry: bool
    image_url: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
