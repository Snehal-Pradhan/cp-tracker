"""Background data fetching with disk caching."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

from . import config
from .api import codechef, codeforces, contests, leetcode
from .models import Contest, UserStats

PLATFORM_FETCHERS = {
    "codeforces": codeforces.user_stats,
    "leetcode": leetcode.user_stats,
    "codechef": codechef.user_stats,
}

PLATFORM_TITLES = {
    "codeforces": "Codeforces",
    "leetcode": "LeetCode",
    "codechef": "CodeChef",
}

MAX_WORKERS = 4


def stats_from_cache(key: str) -> UserStats | None:
    raw = config.cached_block(key)
    if raw:
        try:
            return UserStats.from_dict(raw)
        except (KeyError, TypeError, ValueError):
            return None
    return None


def contests_from_cache() -> list[Contest]:
    raw = config.cached_block("contests")
    if not raw:
        return []
    try:
        return [Contest.from_dict(d) for d in raw]
    except (KeyError, TypeError, ValueError):
        return []


def _not_configured(key: str) -> UserStats:
    return UserStats(platform=PLATFORM_TITLES[key], handle="", ok=False,
                     error="not configured")


def _fetch_one(key: str, handle: str) -> UserStats:
    try:
        stats = PLATFORM_FETCHERS[key](handle)
        if stats.ok:
            config.save_cache_block(key, stats.to_dict())
        return stats
    except Exception as exc:  # noqa: BLE001 - fall back to stale cache
        stale = config.load_cache().get(key, {}).get("data")
        if stale:
            try:
                return UserStats.from_dict(stale)
            except Exception:  # noqa: BLE001, S110 - corrupted cache: fall through
                pass
        return UserStats(platform=PLATFORM_TITLES[key], handle=handle,
                         ok=False, error=str(exc))


def refresh_stats() -> dict[str, UserStats]:
    cfg = config.load_config()
    results = {}
    work = {}
    for key, fetch in PLATFORM_FETCHERS.items():
        handle = (cfg.get(key) or "").strip()
        if not handle:
            results[key] = _not_configured(key)
            continue
        work[key] = (fetch, handle)

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        futures = {key: pool.submit(_fetch_one, key, handle)
                   for key, (_, handle) in work.items()}
        for key, fut in futures.items():
            try:
                results[key] = fut.result(timeout=45)
            except Exception as exc:  # noqa: BLE001
                results[key] = UserStats(platform=PLATFORM_TITLES[key],
                                         handle=work[key][1], ok=False,
                                         error=str(exc))
    return results


def refresh_contests() -> list[Contest]:
    lst = contests.fetch_all_contests()
    config.save_cache_block("contests", [c.to_dict() for c in lst])
    return lst