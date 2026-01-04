# src/scheduling/__init__.py

from datetime import datetime
from scheduling.calendar import is_correct_week
from scheduling.windows import is_within_locked_window


def can_dispatch(job_window_key: str, meta: dict, now: datetime) -> bool:
    """
    Central Phase 10 guardrail.
    Returns True only if:
    - package_ready == True
    - correct ISO week
    - within locked time window
    """
    try:
        release = meta.get("release", {})
        if release.get("package_ready") is not True:
            return False

        week_id = release.get("week_id")
        if not is_correct_week(week_id, now):
            return False

        if not is_within_locked_window(job_window_key, now):
            return False

        return True
    except Exception:
        # Phase 10 must NEVER crash the pipeline
        return False
