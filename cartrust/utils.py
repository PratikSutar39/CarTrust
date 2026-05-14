"""
CarTrust Utilities

Helper functions used across extraction modules and reasoning engine.
"""

import re
import statistics
from datetime import date, datetime
from typing import Optional


def normalize(name: str) -> str:
    """Normalize a name for comparison: lowercase, strip whitespace, remove punctuation."""
    if not name:
        return ""
    return re.sub(r"[^a-z0-9 ]", "", name.lower().strip())


def parse_date(date_str: Optional[str]) -> Optional[datetime]:
    """Parse a date string into a datetime object. Returns None if unparseable."""
    if not date_str:
        return None
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(str(date_str), fmt)
        except ValueError:
            continue
    return None


def today() -> datetime:
    """Return current datetime. Centralised so tests can monkey-patch it."""
    return datetime.now()


def median(values: list) -> float:
    """Return the median of a list of numbers. Raises ValueError if list is empty."""
    if not values:
        raise ValueError("Cannot compute median of empty list")
    return statistics.median(values)


def years_between(start_str: str, end_dt: datetime) -> float:
    """Compute fractional years between a date string and an end datetime."""
    start_dt = parse_date(start_str)
    if not start_dt:
        return 0.0
    delta = end_dt - start_dt
    return delta.days / 365.25


def months_between(start_dt: datetime, end_dt: datetime) -> float:
    """Compute fractional months between two datetimes."""
    return (end_dt - start_dt).days / 30.0


def find_service_entry_near_date(service_log: list, target_date_str: str, window_days: int) -> Optional[dict]:
    """
    Find the first service entry within `window_days` of `target_date_str`.
    Returns the matching entry dict, or None if none found.
    """
    target_dt = parse_date(target_date_str)
    if not target_dt:
        return None
    for entry in service_log:
        entry_dt = parse_date(entry.get("date"))
        if entry_dt and abs((entry_dt - target_dt).days) <= window_days:
            return entry
    return None
