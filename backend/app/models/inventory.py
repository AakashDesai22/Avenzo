"""
AVENZO Backend — Batch, Inventory, and Inventory Transaction Models
ORM definitions for Inventory management foundation.
"""

from sqlalchemy import Column, String, ForeignKey, Text, Integer, Date, DateTime, UniqueConstraint, Index
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base
from app.models.base import UUIDMixin, TimestampMixin, utc_now


class Batch(Base, UUIDMixin, TimestampMixin):
    """Batch entity tracking product manufacturing and expiry dates."""
    __tablename__ = "batches"
    __table_args__ = (
        UniqueConstraint("product_id", "batch_number", name="uq_product_batch_number"),
        Index("ix_batches_fefo_sort", "expiry_date", "created_at"),
    )

    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False, index=True)
    batch_number = Column(String(100), nullable=False, index=True)
    manufacturing_date = Column(Date, nullable=True)
    expiry_date = Column(Date, nullable=True, index=True)
    supplier_id = Column(UUID(as_uuid=True), ForeignKey("suppliers.id"), nullable=True)
    initial_quantity = Column(Integer, nullable=False, default=0)
    status = Column(String(30), nullable=False, default="active") # active, expired, depleted, recalled
    notes = Column(Text, nullable=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    product = relationship("Product", back_populates="batches")
    supplier = relationship("Supplier", back_populates="batches")
    inventories = relationship("Inventory", back_populates="batch")


class Inventory(Base, UUIDMixin, TimestampMixin):
    """Inventory balance tracking stock on hand per product, batch, warehouse, and location."""
    __tablename__ = "inventory"
    __table_args__ = (
        UniqueConstraint("batch_id", "warehouse_id", "location_id", name="uq_inventory_batch_warehouse_location"),
    )

    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False, index=True)
    batch_id = Column(UUID(as_uuid=True), ForeignKey("batches.id"), nullable=False, index=True)
    warehouse_id = Column(UUID(as_uuid=True), ForeignKey("warehouses.id"), nullable=False, index=True)
    location_id = Column(UUID(as_uuid=True), ForeignKey("warehouse_locations.id"), nullable=True)
    quantity_on_hand = Column(Integer, nullable=False, default=0)
    quantity_reserved = Column(Integer, nullable=False, default=0)

    product = relationship("Product", back_populates="inventories")
    batch = relationship("Batch", back_populates="inventories")
    warehouse = relationship("Warehouse", back_populates="inventories")
    location = relationship("WarehouseLocation", back_populates="inventories")
    transactions = relationship("InventoryTransaction", back_populates="inventory")

    @property
    def quantity_available(self) -> int:
        """Returns current available stock (on_hand - reserved)."""
        return max(0, (self.quantity_on_hand or 0) - (self.quantity_reserved or 0))


class InventoryTransaction(Base, UUIDMixin):
    """Audit log tracking every stock movement."""
    __tablename__ = "inventory_transactions"

    inventory_id = Column(UUID(as_uuid=True), ForeignKey("inventory.id"), nullable=False, index=True)
    transaction_type = Column(String(50), nullable=False, index=True) 
    # Types: RECEIPT, ADJUSTMENT, TRANSFER, RESERVATION, RELEASE, SALE, DAMAGE, EXPIRY
    quantity_change = Column(Integer, nullable=False) # Positive = in, Negative = out
    quantity_before = Column(Integer, nullable=False)
    quantity_after = Column(Integer, nullable=False)
    reference_id = Column(UUID(as_uuid=True), nullable=True)
    reference_type = Column(String(50), nullable=True)
    notes = Column(Text, nullable=True)
    performed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)

    inventory = relationship("Inventory", back_populates="transactions")
