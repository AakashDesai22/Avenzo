"""
AVENZO Backend — Consumer Digital Pantry Pydantic Schemas
"""

from uuid import UUID
from datetime import datetime, date
from typing import Optional
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.product import ProductRead


class ConsumerPantryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    name: str
    is_default: bool
    created_at: datetime
    updated_at: datetime


class PantryItemCreate(BaseModel):
    pantry_id: Optional[UUID] = None
    product_id: Optional[UUID] = None
    batch_id: Optional[UUID] = None
    custom_name: Optional[str] = Field(None, max_length=255)
    barcode: Optional[str] = Field(None, max_length=100)
    quantity: Decimal = Field(default=Decimal("1.0"), gt=0)
    unit: str = Field(default="units", max_length=50)
    purchase_date: Optional[date] = None
    expiry_date: Optional[date] = None
    storage_location: str = Field(default="pantry", pattern="^(pantry|fridge|freezer)$")
    notes: Optional[str] = None


class PantryItemUpdate(BaseModel):
    custom_name: Optional[str] = Field(None, max_length=255)
    quantity: Optional[Decimal] = Field(None, gt=0)
    unit: Optional[str] = Field(None, max_length=50)
    purchase_date: Optional[date] = None
    expiry_date: Optional[date] = None
    storage_location: Optional[str] = Field(None, pattern="^(pantry|fridge|freezer)$")
    notes: Optional[str] = None


class PantryItemActionRequest(BaseModel):
    quantity: Decimal = Field(..., gt=0)


class PantryItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    pantry_id: UUID
    product_id: Optional[UUID] = None
    product: Optional[ProductRead] = None
    batch_id: Optional[UUID] = None
    batch_number: Optional[str] = None
    order_item_id: Optional[UUID] = None
    custom_name: Optional[str] = None
    barcode: Optional[str] = None
    quantity: Decimal
    unit: str
    purchase_date: Optional[date] = None
    expiry_date: Optional[date] = None
    storage_location: str
    status: str
    is_recalled: bool = False
    recalled_at: Optional[datetime] = None
    recall_reason: Optional[str] = None
    notes: Optional[str] = None
    days_to_expiry: Optional[int] = None
    expiry_status: str = "N/A"
    created_at: datetime
    updated_at: datetime

    @property
    def display_name(self) -> str:
        if self.product and self.product.name:
            return self.product.name
        return self.custom_name or "Unidentified Item"
