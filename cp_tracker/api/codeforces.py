"""Codeforces API access."""

from datetime import datetime, timezone

from .common import http_json, FetchError
from ..models import Contest, ContestResult, RatingPoint, UserStats

API = "https://codeforces.com/api"


def upcoming_contests() -> list[Contest]:
    data = http_json(f"{API}/contest.list", params={"gym": "false"})
    if data.get("status") != "OK":
        raise FetchError(data.get("comment", "unknown CF error"))
    out = []
    for c in data.get("result", []):
        if c.get("phase") != "BEFORE":
            continue
        start = datetime.fromtimestamp(c["startTimeSeconds"], tz=timezone.utc)
        out.append(Contest(
            platform="Codeforces",
            name=c["name"],
            start_time=start,
            duration_minutes=c.get("durationSeconds", 0) // 60,
            url=f"https://codeforces.com/contestRegistration/{c.get('id', '')}",
            id=str(c.get("id", "")),
        ))
    out.sort(key=lambda c: c.start_time)
    return out


def user_stats(handle: str) -> UserStats:
    try:
        info = http_json(f"{API}/user.info", params={"handles": handle})
    except FetchError as exc:
        return UserStats(platform="Codeforces", handle=handle, ok=False,
                         error=str(exc))
    if info.get("status") != "OK":
        return UserStats(platform="Codeforces", handle=handle, ok=False,
                         error=info.get("comment", "not found"))

    u = info["result"][0]
    history: list[RatingPoint] = []
    results: list[ContestResult] = []
    try:
        rh = http_json(f"{API}/user.rating", params={"handle": handle})
        for r in rh.get("result", []):
            t = datetime.fromtimestamp(r["ratingUpdateTimeSeconds"],
                                       tz=timezone.utc)
            history.append(RatingPoint(t, r["newRating"]))
            results.append(ContestResult(t, r.get("contestName", ""),
                                         r.get("rank", 0),
                                         r["newRating"] - r["oldRating"]))
    except FetchError:
        pass

    rating = u.get("rating")
    return UserStats(
        platform="Codeforces",
        handle=handle,
        ok=True,
        rating=rating,
        max_rating=u.get("maxRating"),
        rank=u.get("rank") if rating else None,
        contests_attended=len(history),
        history=history,
        results=results,
        extra={
            "country": u.get("country"),
            "organization": u.get("organization"),
            "contribution": u.get("contribution"),
            "max_rank": u.get("maxRank"),
        },
    )