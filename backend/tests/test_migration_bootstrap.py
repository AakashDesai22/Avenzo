"""
AVENZO Backend — Unit Tests for Production Migration Bootstrap Utility
Validates safe baseline detection, legacy database stamping, empty database migration,
asyncpg URL normalization, and event loop isolation preventing nested asyncio.run errors.
"""

import pytest
import asyncio
import os
import tempfile
import sqlalchemy as sa
from unittest.mock import patch
from sqlalchemy import create_engine, text
from alembic.config import Config
from alembic import command
from app.core.migration_bootstrap import inspect_and_detect_baseline, run_bootstrap, normalize_async_url


def test_url_normalization_asyncpg():
    """Verify that postgres:// and postgresql:// URLs normalize to postgresql+asyncpg:// without requiring psycopg2."""
    assert normalize_async_url("postgres://user:pass@localhost:5432/db") == "postgresql+asyncpg://user:pass@localhost:5432/db"
    assert normalize_async_url("postgresql://user:pass@localhost:5432/db") == "postgresql+asyncpg://user:pass@localhost:5432/db"
    assert normalize_async_url("postgresql+asyncpg://user:pass@localhost:5432/db") == "postgresql+asyncpg://user:pass@localhost:5432/db"
    assert normalize_async_url("sqlite:///avenzo.db") == "sqlite+aiosqlite:///avenzo.db"
    assert normalize_async_url("sqlite+aiosqlite:///avenzo.db") == "sqlite+aiosqlite:///avenzo.db"


def test_scenario_a_empty_database():
    """Scenario A: Empty database with no tables returns EMPTY_DATABASE baseline."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name

    try:
        async_url = f"sqlite+aiosqlite:///{db_path}"
        status, revision = asyncio.run(inspect_and_detect_baseline(async_url))
        assert status == "EMPTY_DATABASE"
        assert revision is None
    finally:
        if os.path.exists(db_path):
            os.remove(db_path)


def test_scenario_b_legacy_database_detection():
    """Scenario B: Legacy database with notification tables detects revision 6a0199b8d4e2."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name

    try:
        sync_url = f"sqlite:///{db_path}"
        async_url = f"sqlite+aiosqlite:///{db_path}"

        # Create legacy base tables using sync driver
        engine = create_engine(sync_url)
        with engine.begin() as conn:
            conn.execute(text("CREATE TABLE users (id TEXT PRIMARY KEY)"))
            conn.execute(text("CREATE TABLE brands (id TEXT PRIMARY KEY)"))
            conn.execute(text("CREATE TABLE consumer_pantries (id TEXT PRIMARY KEY)"))
            conn.execute(text("CREATE TABLE pantry_items (id TEXT PRIMARY KEY)"))
            conn.execute(text("CREATE TABLE consumer_recommendations (id TEXT PRIMARY KEY)"))
            conn.execute(text("CREATE TABLE notification_records (id TEXT PRIMARY KEY)"))
        engine.dispose()

        status, revision = asyncio.run(inspect_and_detect_baseline(async_url))
        assert status == "DETECTED_BASELINE"
        assert revision == "6a0199b8d4e2"
    finally:
        if os.path.exists(db_path):
            os.remove(db_path)


def test_scenario_c_current_database():
    """Scenario C: Already stamped database returns ALREADY_STAMPED status."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name

    try:
        sync_url = f"sqlite:///{db_path}"
        async_url = f"sqlite+aiosqlite:///{db_path}"

        engine = create_engine(sync_url)
        with engine.begin() as conn:
            conn.execute(text("CREATE TABLE alembic_version (version_num VARCHAR(32) NOT NULL)"))
            conn.execute(text("INSERT INTO alembic_version VALUES ('a12b34c56d7e')"))
        engine.dispose()

        status, revision = asyncio.run(inspect_and_detect_baseline(async_url))
        assert status == "ALREADY_STAMPED"
        assert revision == "a12b34c56d7e"
    finally:
        if os.path.exists(db_path):
            os.remove(db_path)


def test_scenario_d_unmatched_schema():
    """Scenario D: Database with unknown schema returns UNMATCHED_SCHEMA status."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name

    try:
        sync_url = f"sqlite:///{db_path}"
        async_url = f"sqlite+aiosqlite:///{db_path}"

        engine = create_engine(sync_url)
        with engine.begin() as conn:
            conn.execute(text("CREATE TABLE unknown_custom_table (id TEXT PRIMARY KEY)"))
        engine.dispose()

        status, revision = asyncio.run(inspect_and_detect_baseline(async_url))
        assert status == "UNMATCHED_SCHEMA"
        assert revision is None
    finally:
        if os.path.exists(db_path):
            os.remove(db_path)


def test_no_running_event_loop_during_alembic_commands():
    """Regression Test: Verify command.stamp and command.upgrade run with NO active event loop."""
    loop_during_stamp = None
    loop_during_upgrade = None

    def fake_stamp(cfg, rev):
        nonlocal loop_during_stamp
        try:
            loop_during_stamp = asyncio.get_running_loop()
        except RuntimeError:
            loop_during_stamp = "NO_LOOP"

    def fake_upgrade(cfg, target):
        nonlocal loop_during_upgrade
        try:
            loop_during_upgrade = asyncio.get_running_loop()
        except RuntimeError:
            loop_during_upgrade = "NO_LOOP"

    with patch("alembic.command.stamp", side_effect=fake_stamp), \
         patch("alembic.command.upgrade", side_effect=fake_upgrade), \
         patch("app.core.migration_bootstrap.inspect_and_detect_baseline", return_value=("DETECTED_BASELINE", "6a0199b8d4e2")):
        run_bootstrap()

    assert loop_during_stamp == "NO_LOOP"
    assert loop_during_upgrade == "NO_LOOP"
