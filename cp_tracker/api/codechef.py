"""CodeChef API access (scraped / unofficial endpoints)."""

from __future__ import annotations

import re
from datetime import datetime, timezone

from ..models import Contest, UserStats
from .common import FetchError, http_get, http_json

PROFILE = "https://www.codechef.com/users/{handle}"


def stars_from_rating(rating: int | None) -> int:
    if not rating:
        return 0
    if rating >= 2500:
        return 7
    if rating >= 2200:
        return 6
    if rating >= 2000:
        return 5
    if rating >= 1800:
        return 4
    if rating >= 1600:
        return 3
    if rating >= 1500:
        return 2
    if rating >= 1400:
        return 1
    return 0


def upcoming_contests() -> list[Contest]:
    url = ("https://www.codechef.com/api/list/contests/all"
           "?sort_by=START&sorting_order=asc&offset=0&mode=all")
    data = http_json(url, headers={"Referer": "https://www.codechef.com/"})
    if data.get("status") != "success":
        raise FetchError("failed to load CodeChef contests")

    out = []
    for c in data.get("future_contests", []):
        try:
            start = datetime.fromisoformat(c["contest_start_date_iso"])
            end = datetime.fromisoformat(c["contest_end_date_iso"])
        except (KeyError, ValueError):
            continue
        code = c.get("contest_code", "")
        name = c.get("contest_name") or code
        out.append(Contest(
            platform="CodeChef",
            name=name,
            start_time=start.astimezone(timezone.utc),
            duration_minutes=max(1, int((end - start).total_seconds() // 60)),
            url=f"https://www.codechef.com/{code}",
            id=code,
        ))
    out.sort(key=lambda c: c.start_time)
    return out


def _text_of(html: str, pattern: str, group: int = 1):
    m = re.search(pattern, html, re.DOTALL)
    if not m:
        return None
    return re.sub(r"\s+", " ", m.group(group)).strip()


def _rank_listed(html: str, label: str):
    i = html.find(label)
    if i < 0:
        return None
    window = html[max(0, i - 400):i]
    m = re.search(r"<strong>\s*([^<]{1,40}?)\s*</strong>", window, re.DOTALL)
    if not m:
        return None
    val = m.group(1).strip()
    return None if val.lower() in ("inactive", "na", "unrated") else val


def user_stats(handle: str) -> UserStats:
    try:
        resp = http_get(PROFILE.format(handle=handle),
                        headers={"Referer": "https://www.codechef.com/"})
    except FetchError as exc:
        return UserStats(platform="CodeChef", handle=handle, ok=False,
                         error=str(exc))

    html = resp.text
    if resp.status_code != 200 or "rating-number" not in html:
        return UserStats(platform="CodeChef", handle=handle, ok=False,
                         error="handle not found")

    rating_txt = _text_of(html, r'rating-number[^>]*>\s*([0-9NA]+)')
    rating = None
    if rating_txt and rating_txt.isdigit():
        rating = int(rating_txt)

    highest_txt = _text_of(html, r"Highest Rating\s*(\d+)")
    highest = int(highest_txt) if highest_txt else None

    star_count = len(re.findall(r"&#9733;", html))
    if not star_count:
        star_count = stars_from_rating(rating)

    def rank_number(val):
        if not val:
            return None
        digits = re.sub(r"[^0-9]", "", val)
        return int(digits) if digits else None

    global_rank = rank_number(_rank_listed(html, "Global Rank"))
    country_rank = rank_number(_rank_listed(html, "Country Rank"))

    return UserStats(
        platform="CodeChef",
        handle=handle,
        ok=True,
        rating=rating,
        max_rating=highest,
        rank=(("\u2605" * star_count) if star_count else None),
        global_rank=global_rank,
        country_rank=country_rank,
        extra={"stars": star_count, "highest": highest},
    )