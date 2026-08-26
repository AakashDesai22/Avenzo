"""
AVENZO Backend — Consumer Digital Pantry Models
ConsumerPantry, PantryItem, and PantryItemLog ORM definitions.
"""

from sqlalchemy import Column, String, ForeignKey, Text, Date, DateTime, Numeric, Boolean, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base
from app.models.base import UUIDMixin, TimestampMixin, SoftDeleteMixin, utc_now


class ConsumerPantry(Base, UUIDMixin, TimestampMixin):
    """Consumer Pantry entity representing household storage unit."""
    __tablename__ = "consumer_pantries"
    __table_args__ = (
        UniqueConstraint("user_id", "name", name="uq_user_pantry_name"),
    )

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(100), nullable=False, default="My Home Pantry")
    is_default = Column(Boolean, default=True, nullable=False)

    user = relationship("User", backref="pantries")
    items = relationship("PantryItem", back_populates="pantry", cascade="all, delete-orphan")


class PantryItem(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """Pantry Item entity tracking consumer products and expiry dates."""
    __tablename__ = "pantry_items"

    pantry_id = Column(UUID(as_uuid=True), ForeignKey("consumer_pantries.id"), nullable=False, index=True)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=True, index=True)
    batch_id = Column(UUID(as_uuid=True), ForeignKey("batches.id"), nullable=True, index=True)
    order_item_id = Column(UUID(as_uuid=True), ForeignKey("order_items.id", ondelete="SET NULL"), nullable=True, index=True)
    custom_name = Column(String(255), nullable=True)
    barcode = Column(String(100), nullable=True, index=True)
    quantity = Column(Numeric(10, 2), nullable=False, default=1.0)
    unit = Column(String(50), nullable=False, default="units")
    purchase_date = Column(Date, nullable=True)
    expiry_date = Column(Date, nullable=True, index=True)
    storage_location = Column(String(50), nullable=False, default="pantry") # 'pantry', 'fridge', 'freezer'
    status = Column(String(30), nullable=False, default="active", index=True) # 'active', 'consumed', 'discarded', 'expired'
    is_recalled = Column(Boolean, nullable=False, default=False, index=True)
    recalled_at = Column(DateTime(timezone=True), nullable=True)
    recall_reason = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)

    pantry = relationship("ConsumerPantry", back_populates="items")
    product = relationship("Product")
    batch = relationship("Batch")
    order_item = relationship("OrderItem")
    logs = relationship("PantryItemLog", back_populates="pantry_item", cascade="all, delete-orphan")


class PantryItemLog(Base, UUIDMixin):
    """Audit log tracking pantry item actions (ADDED, CONSUMED, DISCARDED, etc)."""
    __tablename__ = "pantry_item_logs"

    pantry_item_id = Column(UUID(as_uuid=True), ForeignKey("pantry_items.id"), nullable=False, index=True)
    action = Column(String(50), nullable=False, index=True)
    # Actions: ADDED, CONSUMED, DISCARDED, EXPIRED_REMOVED, QUANTITY_ADJUSTED
    quantity_change = Column(Numeric(10, 2), nullable=False)
    logged_at = Column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)

    pantry_item = relationship("PantryItem", back_populates="logs")
