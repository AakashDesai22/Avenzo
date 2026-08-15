"""
AVENZO Backend — Base ORM Mixins
Provides reusable UUID primary key, UTC timestamps, and soft delete fields.
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID


def utc_now() -> datetime:
    """Returns current UTC datetime with timezone info."""
    return datetime.now(timezone.utc)


class UUIDMixin:
    """Mixin providing UUID primary key."""
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )


class TimestampMixin:
    """Mixin providing created_at and updated_at UTC timestamps."""
    created_at = Column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )


class SoftDeleteMixin:
    """Mixin providing soft delete flag and timestamps."""
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    deleted_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
