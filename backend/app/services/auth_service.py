"""
AVENZO Backend — Authentication Service
Handles User Registration, Credential Validation, JWT Token Issuance, and Role Seeding.
"""

from typing import Tuple, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from fastapi import HTTPException, status

from app.models.user import User, Role
from app.schemas.auth import RegisterRequest, LoginRequest
from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token, decode_token

DEFAULT_ROLES = {
    "ADMIN": "System Administrator with full permissions",
    "BUSINESS_MANAGER": "Manager for Business Web platform operations",
    "STAFF": "Staff member for warehouse/inventory management",
    "CONSUMER": "Consumer app end-user",
}


async def ensure_roles_seeded(session: AsyncSession) -> None:
    """Ensure default system roles exist in the database."""
    for role_name, description in DEFAULT_ROLES.items():
        result = await session.execute(select(Role).where(Role.name == role_name))
        existing_role = result.scalars().first()
        if not existing_role:
            new_role = Role(name=role_name, description=description)
            session.add(new_role)
    await session.commit()


async def register_user(session: AsyncSession, request: RegisterRequest) -> User:
    """Registers a new user and returns the created user entity."""
    await ensure_roles_seeded(session)

    # Check for existing email
    result = await session.execute(select(User).where(User.email == request.email.lower()))
    if result.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"User with email '{request.email}' already exists.",
        )

    # Assign default role based on user_type
    target_role_name = "CONSUMER" if request.user_type == "consumer" else "STAFF"
    role_result = await session.execute(select(Role).where(Role.name == target_role_name))
    role = role_result.scalars().first()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Default role '{target_role_name}' could not be initialized.",
        )

    user = User(
        email=request.email.lower(),
        password_hash=hash_password(request.password),
        first_name=request.first_name,
        last_name=request.last_name,
        phone=request.phone,
        role_id=role.id,
        user_type=request.user_type,
        is_active=True,
    )

    session.add(user)
    await session.commit()
    await session.refresh(user)

    # Load role relationship
    result = await session.execute(
        select(User).options(joinedload(User.role)).where(User.id == user.id)
    )
    return result.scalars().first()


async def authenticate_user(session: AsyncSession, request: LoginRequest) -> Tuple[User, str, str]:
    """
    Validates user credentials and returns (User, access_token, refresh_token).
    Raises HTTP 401 if invalid.
    """
    result = await session.execute(
        select(User).options(joinedload(User.role)).where(User.email == request.email.lower())
    )
    user = result.scalars().first()

    if not user or user.is_deleted or not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive.",
        )

    access_token = create_access_token(subject=str(user.id), role=user.role.name if user.role else "CONSUMER")
    refresh_token = create_refresh_token(subject=str(user.id))

    return user, access_token, refresh_token


async def refresh_access_token(session: AsyncSession, refresh_token_str: str) -> Tuple[str, User]:
    """Validates refresh token and issues a new access token."""
    payload = decode_token(refresh_token_str)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token.",
        )

    user_id = payload.get("sub")
    result = await session.execute(
        select(User).options(joinedload(User.role)).where(User.id == user_id)
    )
    user = result.scalars().first()

    if not user or not user.is_active or user.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is no longer active.",
        )

    new_access_token = create_access_token(subject=str(user.id), role=user.role.name if user.role else "CONSUMER")
    return new_access_token, user
