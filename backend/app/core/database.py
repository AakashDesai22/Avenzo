"""
AVENZO Backend — Database Core Configuration
SQLAlchemy 2.x Async Engine, Session Factory, Base Declarative Class, and Dependency Injection.
"""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase
from app.core.config import settings

# Configure engine kwargs based on database dialect
engine_kwargs = {"echo": False, "future": True}
if settings.DATABASE_URL.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    engine_kwargs["pool_pre_ping"] = True

# Create async engine
async_engine = create_async_engine(
    settings.DATABASE_URL,
    **engine_kwargs,
)

# Async session factory
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


class Base(DeclarativeBase):
    """Base declarative class for all SQLAlchemy ORM models."""
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that provides an async database session per request.
    Ensures session is properly closed after request completion.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
