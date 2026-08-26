"""
AVENZO Backend — Order Batch Allocation Model
Tracks exact FEFO inventory batch allocations per OrderItem for batch traceability.
"""

from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base
from app.models.base import UUIDMixin, TimestampMixin


class OrderBatchAllocation(Base, UUIDMixin, TimestampMixin):
    """Batch-level allocation entity linking an OrderItem to a specific inventory batch."""
    __tablename__ = "order_batch_allocations"

    order_item_id = Column(UUID(as_uuid=True), ForeignKey("order_items.id", ondelete="CASCADE"), nullable=False, index=True)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True)
    batch_id = Column(UUID(as_uuid=True), ForeignKey("batches.id", ondelete="RESTRICT"), nullable=False, index=True)
    inventory_id = Column(UUID(as_uuid=True), ForeignKey("inventory.id", ondelete="RESTRICT"), nullable=False, index=True)
    allocated_quantity = Column(Integer, nullable=False)

    order_item = relationship("OrderItem", back_populates="allocations")
    order = relationship("Order", back_populates="allocations")
    product = relationship("Product")
    batch = relationship("Batch")
    inventory = relationship("Inventory")
