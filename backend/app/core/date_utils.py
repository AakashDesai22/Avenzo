"""
AVENZO Backend — Centralized Business Date Utility
Provides consistent UTC business date and datetime handling across services.
"""

from datetime import date, datetime, timezone


def get_business_date() -> date:
    """
    Returns the current business UTC date.
    Centralized abstraction for expiry calculations to prevent scattered datetime calls.
    """
    return datetime.now(timezone.utc).date()


def get_utc_now() -> datetime:
    """Returns current UTC datetime with timezone info."""
    return datetime.now(timezone.utc)
