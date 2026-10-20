"""
AVENZO Backend — Product & Brand Pydantic Schemas
"""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.category import CategoryRead


class BrandRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: str | None = None
    logo_url: str | None = None


class ProductCreate(BaseModel):
    name: str = Field(..., max_length=255)
    description: str | None = None
    sku: str = Field(..., max_length=100)
    barcode: str | None = Field(None, max_length=100)
    category_id: UUID
    brand_id: UUID | None = None
    unit_of_measure: str = Field(default="units", max_length=50)
    unit_price: Decimal = Field(..., ge=0)
    cost_price: Decimal | None = Field(None, ge=0)
    reorder_point: int | None = Field(None, ge=0)
    reorder_quantity: int | None = Field(None, ge=0)
    shelf_life_days: int | None = Field(None, ge=0)
    has_expiry: bool = True
    image_url: str | None = Field(None, max_length=500)
    is_active: bool = True
    is_published: bool = False


class ProductUpdate(BaseModel):
    name: str | None = Field(None, max_length=255)
    description: str | None = None
    sku: str | None = Field(None, max_length=100)
    barcode: str | None = Field(None, max_length=100)
    category_id: UUID | None = None
    brand_id: UUID | None = None
    unit_of_measure: str | None = Field(None, max_length=50)
    unit_price: Decimal | None = Field(None, ge=0)
    cost_price: Decimal | None = Field(None, ge=0)
    reorder_point: int | None = Field(None, ge=0)
    reorder_quantity: int | None = Field(None, ge=0)
    shelf_life_days: int | None = Field(None, ge=0)
    has_expiry: bool | None = None
    image_url: str | None = Field(None, max_length=500)
    is_active: bool | None = None
    is_published: bool | None = None


class ProductRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: str | None = None
    sku: str
    barcode: str | None = None
    category_id: UUID
    category: CategoryRead | None = None
    brand_id: UUID | None = None
    brand: BrandRead | None = None
    unit_of_measure: str
    unit_price: Decimal
    cost_price: Decimal | None = None
    reorder_point: int | None = None
    reorder_quantity: int | None = None
    shelf_life_days: int | None = None
    has_expiry: bool
    image_url: str | None = None
    is_active: bool
    is_published: bool
    created_at: datetime
    updated_at: datetime
