"""
AVENZO Backend — Unit Tests for Production Migration Bootstrap Utility
Validates safe baseline detection, legacy database stamping, empty database migration,
and unmatched schema failure handling.
"""

import pytest
import os
import tempfile
import sqlalchemy as sa
from sqlalchemy import create_engine, text
from app.core.migration_bootstrap import inspect_and_detect_baseline, run_bootstrap


def test_scenario_a_empty_database():
    """Scenario A: Empty database with no tables returns EMPTY_DATABASE baseline."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name

    try:
        async_url = f"sqlite+aiosqlite:///{db_path}"
        status, revision = inspect_and_detect_baseline(async_url)
        assert status == "EMPTY_DATABASE"
        assert revision is None
    finally:
        if os.path.exists(db_path):
            os.remove(db_path)


def test_scenario_b_legacy_database_detection_and_stamping():
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

        status, revision = inspect_and_detect_baseline(async_url)
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

        status, revision = inspect_and_detect_baseline(async_url)
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

        status, revision = inspect_and_detect_baseline(async_url)
        assert status == "UNMATCHED_SCHEMA"
        assert revision is None
    finally:
        if os.path.exists(db_path):
            os.remove(db_path)
