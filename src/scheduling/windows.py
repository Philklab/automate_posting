# src/scheduling/windows.py

from datetime import datetime, timedelta, time
from zoneinfo import ZoneInfo

# Phase 7 — LOCKED WINDOWS
# weekday: Monday=0 ... Sunday=6
WINDOWS = {
    "full": {
        "weekday": 1,   # Tuesday
        "time": time(13, 0),
        "tolerance_min": 30,
    },
    "short_01": {
        "weekday": 3,   # Thursday
        "time": time(19, 0),
        "tolerance_min": 30,
    },
    "short_02": {
        "weekday": 6,   # Sunday
        "time": time(11, 0),
        "tolerance_min": 30,
    },
}


def is_within_locked_window(
    window_key: str,
    now: datetime,
    tz_name: str = "America/New_York",
) -> bool:
    """
    Returns True if 'now' is within the locked posting window.
    Silent False if window_key is unknown or out of window.
    """
    if window_key not in WINDOWS:
        return False

    tz = ZoneInfo(tz_name)
    if now.tzinfo is None:
        now = now.replace(tzinfo=tz)
    else:
        now = now.astimezone(tz)

    cfg = WINDOWS[window_key]

    if now.weekday() != cfg["weekday"]:
        return False

    target_dt = datetime.combine(
        now.date(),
        cfg["time"],
        tzinfo=tz,
    )

    tolerance = timedelta(minutes=cfg["tolerance_min"])
    delta = abs(now - target_dt)

    return delta <= tolerance
