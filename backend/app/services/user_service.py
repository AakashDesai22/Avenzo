"""
AVENZO Backend — User Service
Business logic for managing users and roles.
"""

from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from fastapi import HTTPException, status

from app.models.user import User, Role
from app.schemas.user import UserUpdate


async def get_user_by_id(session: AsyncSession, user_id: UUID) -> User:
    """Get active user by UUID."""
    result = await session.execute(
        select(User).options(joinedload(User.role)).where(User.id == user_id, User.is_deleted == False)
    )
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id '{user_id}' not found.",
        )
    return user


async def list_users(session: AsyncSession, skip: int = 0, limit: int = 50) -> List[User]:
    """List non-deleted users with pagination."""
    result = await session.execute(
        select(User)
        .options(joinedload(User.role))
        .where(User.is_deleted == False)
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().unique().all()


async def update_user(session: AsyncSession, user_id: UUID, update_data: UserUpdate) -> User:
    """Update user properties."""
    user = await get_user_by_id(session, user_id)

    data = update_data.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(user, key, value)

    await session.commit()
    await session.refresh(user)
    return user


async def list_roles(session: AsyncSession) -> List[Role]:
    """List all system roles."""
    result = await session.execute(select(Role))
    return result.scalars().all()
