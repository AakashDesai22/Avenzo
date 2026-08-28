"""
AVENZO Backend — Safe Production Migration Bootstrap Utility
Detects existing database schema baselines asynchronously using the asyncpg/aiosqlite driver
and safely executes Alembic migrations without requiring psycopg2 or causing nested event loop errors.
"""

import sys
import asyncio
import logging
from typing import Tuple, Optional
from sqlalchemy import inspect, text
from sqlalchemy.ext.asyncio import create_async_engine
from alembic.config import Config
from alembic import command
from app.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("migration_bootstrap")


def normalize_async_url(url: str) -> str:
    """Ensure database URL uses the async driver (postgresql+asyncpg:// or sqlite+aiosqlite://)."""
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+asyncpg://", 1)
    if url.startswith("postgresql://") and not url.startswith("postgresql+asyncpg://"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    if url.startswith("sqlite://") and not url.startswith("sqlite+aiosqlite://"):
        return url.replace("sqlite://", "sqlite+aiosqlite://", 1)
    return url


async def inspect_and_detect_baseline(url: str) -> Tuple[str, Optional[str]]:
    """
    Asynchronously inspects existing database tables and columns using run_sync
    to determine if a historical Alembic migration baseline needs to be stamped.
    The async engine is guaranteed to be disposed before returning.
    """
    async_url = normalize_async_url(url)
    engine = create_async_engine(async_url, pool_pre_ping=True)

    try:
        async with engine.connect() as conn:
            def _sync_inspect(sync_conn) -> Tuple[str, Optional[str]]:
                inspector = inspect(sync_conn)
                tables = set(inspector.get_table_names())

                # 1. Check if alembic_version table exists and has a record
                if "alembic_version" in tables:
                    try:
                        res = sync_conn.execute(text("SELECT version_num FROM alembic_version")).fetchone()
                        if res and res[0]:
                            return "ALREADY_STAMPED", res[0]
                    except Exception:
                        pass

                # 2. Database is completely empty?
                if not tables or tables == {"alembic_version"}:
                    return "EMPTY_DATABASE", None

                # 3. Existing tables detected — map to highest matching Alembic revision
                if "pantry_items" in tables:
                    pantry_cols = {c["name"] for c in inspector.get_columns("pantry_items")}
                    if "order_item_id" in pantry_cols:
                        return "DETECTED_BASELINE", "a12b34c56d7e"

                if "order_batch_allocations" in tables:
                    return "DETECTED_BASELINE", "9d0422eb7b85"
                if "orders" in tables:
                    return "DETECTED_BASELINE", "8c0311daF6a4"
                if "carts" in tables:
                    return "DETECTED_BASELINE", "7b0200c9e5f3"
                if "notification_records" in tables:
                    return "DETECTED_BASELINE", "6a0199b8d4e2"
                if "consumer_recommendations" in tables:
                    return "DETECTED_BASELINE", "5f0189a7c3e1"
                if "pantry_items" in tables or "consumer_pantries" in tables:
                    return "DETECTED_BASELINE", "5a0179f8b4d2"
                if "brands" in tables or "users" in tables:
                    return "DETECTED_BASELINE", "f8fe01bb5199"

                return "UNMATCHED_SCHEMA", None

            return await conn.run_sync(_sync_inspect)
    finally:
        await engine.dispose()


def run_bootstrap() -> None:
    """
    Main synchronous migration bootstrap routine called prior to API server startup.
    Executes async schema inspection inside a dedicated asyncio.run() block, ensuring
    the event loop is fully closed before Alembic commands are invoked.
    """
    url = settings.DATABASE_URL
    logger.info("[AVENZO MIGRATION BOOTSTRAP] Evaluating database schema state using async engine...")

    # Dedicated async execution block for schema inspection ONLY
    status, revision = asyncio.run(inspect_and_detect_baseline(url))
    logger.info(f"[AVENZO MIGRATION BOOTSTRAP] Baseline inspection status: {status}, Revision: {revision}")

    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

    if status == "ALREADY_STAMPED":
        logger.info(f"[AVENZO MIGRATION BOOTSTRAP] Database already recorded at revision: {revision}")
    elif status == "EMPTY_DATABASE":
        logger.info("[AVENZO MIGRATION BOOTSTRAP] Empty database detected. Running full migration chain from HEAD...")
    elif status == "DETECTED_BASELINE":
        logger.info(f"[AVENZO MIGRATION BOOTSTRAP] Legacy schema detected! Stamping baseline revision: {revision}")
        command.stamp(alembic_cfg, revision)
        logger.info(f"[AVENZO MIGRATION BOOTSTRAP] Successfully stamped revision {revision}.")
    elif status == "UNMATCHED_SCHEMA":
        logger.error("[AVENZO MIGRATION BOOTSTRAP] CRITICAL: Existing database schema does not match any known Alembic baseline revision!")
        sys.exit(1)

    logger.info("[AVENZO MIGRATION BOOTSTRAP] Running 'alembic upgrade head'...")
    command.upgrade(alembic_cfg, "head")
    logger.info("[AVENZO MIGRATION BOOTSTRAP] Alembic migration upgrade to HEAD complete!")


def main() -> None:
    run_bootstrap()


if __name__ == "__main__":
    main()
