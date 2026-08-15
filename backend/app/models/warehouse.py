"""
AVENZO Backend — Warehouse and Warehouse Location Models
ORM definitions for Warehouse management foundation.
"""

from sqlalchemy import Column, String, Boolean, ForeignKey, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base
from app.models.base import UUIDMixin, TimestampMixin


class Warehouse(Base, UUIDMixin, TimestampMixin):
    """Warehouse facility entity."""
    __tablename__ = "warehouses"

    name = Column(String(150), nullable=False, index=True)
    address = Column(Text, nullable=True)
    city = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    locations = relationship("WarehouseLocation", back_populates="warehouse", cascade="all, delete-orphan")
    inventories = relationship("Inventory", back_populates="warehouse")


class WarehouseLocation(Base, UUIDMixin, TimestampMixin):
    """Specific bin/aisle/shelf location within a warehouse."""
    __tablename__ = "warehouse_locations"
    __table_args__ = (
        UniqueConstraint("warehouse_id", "location_code", name="uq_warehouse_location_code"),
    )

    warehouse_id = Column(UUID(as_uuid=True), ForeignKey("warehouses.id", ondelete="CASCADE"), nullable=False)
    location_code = Column(String(50), nullable=False, index=True) # e.g., 'A-01-02'
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    warehouse = relationship("Warehouse", back_populates="locations")
    inventories = relationship("Inventory", back_populates="location")
