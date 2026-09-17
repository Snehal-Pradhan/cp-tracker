"""Formatting helpers for the TUI."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

PLATFORM_COLORS = {
    "Codeforces": "red",
    "LeetCode": "orange2",
    "CodeChef": "green",
}


def local(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone()


def fmt_dt(dt: datetime) -> str:
    return local(dt).strftime("%Y-%m-%d %H:%M")


def fmt_time(dt: datetime) -> str:
    return local(dt).strftime("%a %d %b %H:%M")


def in_when(dt: datetime, now: datetime | None = None) -> str:
    now = now or datetime.now(timezone.utc)
    delta = local(dt) - local(now)
    if delta.total_seconds() <= 0:
        return "open"
    days = int(delta.total_seconds() // 86400)
    hours = int((delta.total_seconds() % 86400) // 3600)
    mins = int((delta.total_seconds() % 3600) // 60)
    if days > 0:
        return f"in {days}d {hours}h"
    if hours > 0:
        return f"in {hours}h {mins}m"
    return f"in {mins}m"


def dur_mins(duration_minutes: int) -> str:
    h, m = divmod(duration_minutes, 60)
    if h == 0:
        return f"{m}m"
    if m == 0:
        return f"{h}h"
    return f"{h}h{m}m"


def fmt_number(n) -> str:
    if n is None:
        return "—"
    if isinstance(n, int) and n >= 1000:
        return f"{n:,}"
    return str(n)
