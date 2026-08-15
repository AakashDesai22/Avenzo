"""
AVENZO Backend — Test Configuration and Shared Fixtures
Async engine, database session, HTTPX client, and RBAC test user headers.
"""

import pytest
import pytest_asyncio
from typing import AsyncGenerator, Dict
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.future import select
from sqlalchemy.pool import NullPool

from app.main import app
from app.core.config import settings
from app.core.database import Base, get_db
from app.core.security import create_access_token, hash_password
from app.models.user import User, Role
from app.services.auth_service import ensure_roles_seeded

# Test database engine using NullPool to prevent connection reuse conflicts in async tests
test_engine = create_async_engine(settings.DATABASE_URL, echo=False, poolclass=NullPool)
TestingSessionLocal = async_sessionmaker(
    bind=test_engine, class_=AsyncSession, expire_on_commit=False, autoflush=False
)


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_test_db():
    """Drop and recreate DB schema and seed roles before running test suite."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async with TestingSessionLocal() as session:
        await ensure_roles_seeded(session)

    yield


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provides a fresh database session for tests."""
    async with TestingSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """HTTPX AsyncClient overriding get_db dependency."""
    async def _override_get_db() -> AsyncGenerator[AsyncSession, None]:
        async with TestingSessionLocal() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    app.dependency_overrides[get_db] = _override_get_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


async def _create_test_user_with_role(session: AsyncSession, email: str, role_name: str) -> User:
    """Helper to create a user with specified role_name."""
    res = await session.execute(select(User).where(User.email == email))
    existing = res.scalars().first()
    if existing:
        return existing

    role_res = await session.execute(select(Role).where(Role.name == role_name))
    role = role_res.scalars().first()
    if not role:
        role = Role(name=role_name, description=f"{role_name} test role")
        session.add(role)
        await session.flush()

    user = User(
        email=email,
        password_hash=hash_password("TestPassword123!"),
        first_name=role_name.capitalize(),
        last_name="Tester",
        role_id=role.id,
        user_type="business" if role_name != "CONSUMER" else "consumer",
        is_active=True,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


@pytest_asyncio.fixture
async def admin_headers(db_session: AsyncSession) -> Dict[str, str]:
    """Auth headers for ADMIN role user."""
    user = await _create_test_user_with_role(db_session, "admin_test_user@avenzo.dev", "ADMIN")
    token = create_access_token(subject=str(user.id), role="ADMIN")
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def manager_headers(db_session: AsyncSession) -> Dict[str, str]:
    """Auth headers for BUSINESS_MANAGER role user."""
    user = await _create_test_user_with_role(db_session, "manager_test_user@avenzo.dev", "BUSINESS_MANAGER")
    token = create_access_token(subject=str(user.id), role="BUSINESS_MANAGER")
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def staff_headers(db_session: AsyncSession) -> Dict[str, str]:
    """Auth headers for STAFF role user."""
    user = await _create_test_user_with_role(db_session, "staff_test_user@avenzo.dev", "STAFF")
    token = create_access_token(subject=str(user.id), role="STAFF")
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def consumer_headers(db_session: AsyncSession) -> Dict[str, str]:
    """Auth headers for CONSUMER role user."""
    user = await _create_test_user_with_role(db_session, "consumer_test_user@avenzo.dev", "CONSUMER")
    token = create_access_token(subject=str(user.id), role="CONSUMER")
    return {"Authorization": f"Bearer {token}"}
