"""
AVENZO Backend — Category Service
Business logic for managing product categories.
"""

from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException, status

from app.models.product import Category
from app.schemas.category import CategoryCreate, CategoryUpdate


async def create_category(session: AsyncSession, data: CategoryCreate) -> Category:
    """Create a new category."""
    # If parent_id provided, verify parent exists
    if data.parent_id:
        parent_res = await session.execute(select(Category).where(Category.id == data.parent_id))
        if not parent_res.scalars().first():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Parent category with id '{data.parent_id}' not found.",
            )

    category = Category(
        name=data.name,
        parent_id=data.parent_id,
        description=data.description,
        is_active=data.is_active,
    )
    session.add(category)
    await session.commit()
    await session.refresh(category)
    return category


async def get_category_by_id(session: AsyncSession, category_id: UUID) -> Category:
    """Get category by ID."""
    result = await session.execute(select(Category).where(Category.id == category_id))
    category = result.scalars().first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category with id '{category_id}' not found.",
        )
    return category


async def list_categories(session: AsyncSession, active_only: bool = True) -> List[Category]:
    """List categories."""
    stmt = select(Category)
    if active_only:
        stmt = stmt.where(Category.is_active == True)
    result = await session.execute(stmt)
    return result.scalars().all()


async def update_category(session: AsyncSession, category_id: UUID, data: CategoryUpdate) -> Category:
    """Update a category."""
    category = await get_category_by_id(session, category_id)

    update_dict = data.model_dump(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(category, key, value)

    await session.commit()
    await session.refresh(category)
    return category


async def deactivate_category(session: AsyncSession, category_id: UUID) -> Category:
    """Soft deactivate a category."""
    category = await get_category_by_id(session, category_id)
    category.is_active = False
    await session.commit()
    await session.refresh(category)
    return category
