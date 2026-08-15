"""
AVENZO Backend — Category, Brand, and Product Models
ORM model definitions for Product Catalogue foundation.
"""

from sqlalchemy import Column, String, Boolean, ForeignKey, Text, Numeric, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base
from app.models.base import UUIDMixin, TimestampMixin, SoftDeleteMixin


class Category(Base, UUIDMixin, TimestampMixin):
    """Category hierarchy entity for organizing products."""
    __tablename__ = "categories"

    name = Column(String(150), nullable=False, index=True)
    parent_id = Column(UUID(as_uuid=True), ForeignKey("categories.id", ondelete="SET NULL"), nullable=True)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    parent = relationship("Category", remote_side="Category.id", backref="subcategories")
    products = relationship("Product", back_populates="category")


class Brand(Base, UUIDMixin, TimestampMixin):
    """Brand master entity."""
    __tablename__ = "brands"

    name = Column(String(150), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    logo_url = Column(String(500), nullable=True)

    products = relationship("Product", back_populates="brand")


class Product(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """Product master entity representing item catalogue."""
    __tablename__ = "products"

    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    sku = Column(String(100), unique=True, nullable=False, index=True)
    barcode = Column(String(100), unique=True, nullable=True, index=True)
    category_id = Column(UUID(as_uuid=True), ForeignKey("categories.id"), nullable=False)
    brand_id = Column(UUID(as_uuid=True), ForeignKey("brands.id"), nullable=True)
    unit_of_measure = Column(String(50), nullable=False, default="units") # e.g., 'kg', 'units', 'liters'
    unit_price = Column(Numeric(12, 2), nullable=False)
    cost_price = Column(Numeric(12, 2), nullable=True)
    reorder_point = Column(Integer, nullable=True)
    reorder_quantity = Column(Integer, nullable=True)
    shelf_life_days = Column(Integer, nullable=True)
    has_expiry = Column(Boolean, default=True, nullable=False)
    image_url = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    category = relationship("Category", back_populates="products")
    brand = relationship("Brand", back_populates="products")
    batches = relationship("Batch", back_populates="product")
    inventories = relationship("Inventory", back_populates="product")
