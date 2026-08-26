"""
AVENZO Backend — Consumer Order Pydantic Schemas
"""

from uuid import UUID
from datetime import datetime
from typing import List, Optional
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.marketplace import MarketplaceProductRead


class OrderCheckoutRequest(BaseModel):
    """Payload to checkout active consumer cart into a purchase order."""
    shipping_address: str = Field(..., min_length=5, max_length=1000)
    notes: Optional[str] = Field(None, max_length=1000)
    payment_method: str = Field(default="MOCK_PAYMENT", pattern="^(MOCK_PAYMENT|COD)$")


class OrderItemRead(BaseModel):
    """Line item in consumer purchase order with price snapshot."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    order_id: UUID
    product_id: UUID
    quantity: int
    unit_price: Decimal
    total_price: Decimal
    fulfillment_status: str
    product: Optional[MarketplaceProductRead] = None
    created_at: datetime
    updated_at: datetime


class OrderRead(BaseModel):
    """Consumer order details view."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    order_number: str
    user_id: UUID
    status: str
    payment_status: str
    payment_method: str
    subtotal: Decimal
    delivery_fee: Decimal
    total_amount: Decimal
    shipping_address: str
    notes: Optional[str] = None
    items: List[OrderItemRead] = []
    created_at: datetime
    updated_at: datetime
