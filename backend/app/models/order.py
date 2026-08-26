"""
AVENZO Backend — Consumer Order & OrderItem Models
Order and OrderItem ORM definitions for consumer commerce and stock reservation.
"""

from sqlalchemy import Column, String, Numeric, Integer, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base
from app.models.base import UUIDMixin, TimestampMixin, SoftDeleteMixin


class Order(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """Consumer purchase order entity."""
    __tablename__ = "orders"

    order_number = Column(String(50), unique=True, nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String(30), nullable=False, default="PENDING", index=True) 
    # Statuses: PENDING, CONFIRMED, ALLOCATED, PACKED, SHIPPED, DELIVERED, CANCELLED, FAILED
    payment_status = Column(String(30), nullable=False, default="UNPAID") # UNPAID, PAID, REFUNDED
    payment_method = Column(String(30), nullable=False, default="MOCK_PAYMENT") # MOCK_PAYMENT, COD
    subtotal = Column(Numeric(12, 2), nullable=False, default=0.00)
    delivery_fee = Column(Numeric(12, 2), nullable=False, default=0.00)
    total_amount = Column(Numeric(12, 2), nullable=False, default=0.00)
    shipping_address = Column(Text, nullable=False)
    notes = Column(Text, nullable=True)
    idempotency_key = Column(String(100), nullable=True, index=True)

    user = relationship("User", backref="orders", foreign_keys=[user_id])
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    allocations = relationship("OrderBatchAllocation", back_populates="order", cascade="all, delete-orphan")


class OrderItem(Base, UUIDMixin, TimestampMixin):
    """Specific product line item within a consumer order with price snapshot."""
    __tablename__ = "order_items"

    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Numeric(12, 2), nullable=False) # Price snapshot at checkout
    total_price = Column(Numeric(12, 2), nullable=False)
    fulfillment_status = Column(String(30), nullable=False, default="UNALLOCATED") 
    # Statuses: UNALLOCATED, ALLOCATED, PACKED, SHIPPED, DELIVERED

    order = relationship("Order", back_populates="items")
    product = relationship("Product")
    allocations = relationship("OrderBatchAllocation", back_populates="order_item", cascade="all, delete-orphan")
