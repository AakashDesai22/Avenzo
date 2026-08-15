"""
AVENZO Backend — Supplier Master Model
ORM definition for Supplier entity.
"""

from sqlalchemy import Column, String, Boolean, Text
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.base import UUIDMixin, TimestampMixin, SoftDeleteMixin


class Supplier(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """Supplier master entity."""
    __tablename__ = "suppliers"

    name = Column(String(255), nullable=False, index=True)
    contact_person = Column(String(150), nullable=True)
    email = Column(String(255), nullable=True)
    phone = Column(String(20), nullable=True)
    address = Column(Text, nullable=True)
    city = Column(String(100), nullable=True)
    country = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    batches = relationship("Batch", back_populates="supplier")
