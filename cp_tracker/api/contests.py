"""Aggregate upcoming contests from all three platforms."""

from . import codechef, codeforces, leetcode


def fetch_all_contests() -> list:
    contests = []
    for fetch in (codeforces.upcoming_contests,
                  leetcode.upcoming_contests,
                  codechef.upcoming_contests):
        try:
            contests.extend(fetch())
        except Exception:  # noqa: BLE001, S112 - one site failing must not drop the rest
            continue
    contests.sort(key=lambda c: c.start_time)
    return contests