# src/scheduling/calendar.py

from datetime import datetime
import re

WEEK_RE = re.compile(r"^\d{4}-W\d{2}$")


def is_correct_week(release_week_id: str, now: datetime) -> bool:
    """
    Returns True if release_week_id matches the current ISO week.
    Silent failure (returns False) on any invalid input.
    """
    if not release_week_id or not isinstance(release_week_id, str):
        return False

    if not WEEK_RE.match(release_week_id):
        return False

    try:
        iso_year, iso_week, _ = now.isocalendar()
        current = f"{iso_year}-W{iso_week:02d}"
        return release_week_id == current
    except Exception:
        return False
