"""
AVENZO Backend — User & RBAC Models
User, Role, Permission, and RolePermission ORM definitions.
"""

from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text, Table
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base
from app.models.base import UUIDMixin, TimestampMixin, SoftDeleteMixin


class RolePermission(Base):
    """Association table linking Roles to Permissions."""
    __tablename__ = "role_permissions"

    role_id = Column(UUID(as_uuid=True), ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True)
    permission_id = Column(UUID(as_uuid=True), ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True)


class Permission(Base, UUIDMixin):
    """Permission entity defining granular action authorization."""
    __tablename__ = "permissions"

    name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False)

    roles = relationship("Role", secondary="role_permissions", back_populates="permissions")


class Role(Base, UUIDMixin, TimestampMixin):
    """Role entity defining user authorization levels (ADMIN, BUSINESS_MANAGER, STAFF, CONSUMER)."""
    __tablename__ = "roles"

    name = Column(String(50), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)

    users = relationship("User", back_populates="role")
    permissions = relationship("Permission", secondary="role_permissions", back_populates="roles")


class User(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """User entity representing both Business Staff and End Consumers."""
    __tablename__ = "users"

    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    phone = Column(String(20), nullable=True)
    role_id = Column(UUID(as_uuid=True), ForeignKey("roles.id"), nullable=False)
    user_type = Column(String(20), nullable=False, default="consumer") # 'business' or 'consumer'
    is_active = Column(Boolean, default=True, nullable=False)
    last_login_at = Column(DateTime(timezone=True), nullable=True)
    fcm_token = Column(String(500), nullable=True)

    role = relationship("Role", back_populates="users")
