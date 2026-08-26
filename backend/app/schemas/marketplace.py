"""
AVENZO Backend — Consumer Marketplace Pydantic Schemas
Exposes consumer-safe product and availability information while hiding
internal warehouse, batch, cost, and reservation details.
"""

from uuid import UUID
from typing import Optional
from decimal import Decimal
from pydantic import BaseModel, ConfigDict
from app.schemas.category import CategoryRead
from app.schemas.product import BrandRead


class MarketplaceProductRead(BaseModel):
    """
    Consumer-facing Product schema.
    Strictly excludes internal cost prices, reorder thresholds, supplier IDs,
    warehouse locations, batch IDs, and raw inventory reservation fields.
    """
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
    shelf_life_days: Optional[int] = None
    has_expiry: bool
    image_url: Optional[str] = None
    is_active: bool
    available_quantity: int = 0
    is_available: bool = False
