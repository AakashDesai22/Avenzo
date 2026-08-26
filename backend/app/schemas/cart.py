"""
AVENZO Backend — Consumer Cart Pydantic Schemas
"""

from uuid import UUID
from datetime import datetime
from typing import List, Optional
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.marketplace import MarketplaceProductRead


class CartItemAddRequest(BaseModel):
    """Payload to add a product item to consumer cart."""
    product_id: UUID
    quantity: int = Field(default=1, ge=1)


class CartItemUpdateRequest(BaseModel):
    """Payload to update an existing cart item quantity."""
    quantity: int = Field(..., ge=0)


class CartItemRead(BaseModel):
    """Consumer cart item view with nested product and availability status."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    cart_id: UUID
    product_id: UUID
    quantity: int
    product: Optional[MarketplaceProductRead] = None
    created_at: datetime
    updated_at: datetime


class CartRead(BaseModel):
    """Consumer cart view with line items, calculated subtotal, and total item count."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    status: str
    items: List[CartItemRead] = []
    total_items_count: int = 0
    calculated_subtotal: Decimal = Decimal("0.00")
    created_at: datetime
    updated_at: datetime
