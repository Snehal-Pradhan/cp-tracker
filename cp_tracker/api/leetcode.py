"""LeetCode API access (GraphQL)."""

from datetime import datetime, timezone

from ..models import Contest, ContestResult, RatingPoint, UserStats
from .common import FetchError, http_post_json

GQL = "https://leetcode.com/graphql"
CONTEST_URL = "https://leetcode.com/contest/{slug}"


def upcoming_contests() -> list[Contest]:
    body = {"query": "query {\n"
                     "  allContests { title titleSlug startTime duration } }"}
    data = http_post_json(GQL, body)
    contests = data.get("data", {}).get("allContests", [])
    now = datetime.now(timezone.utc).timestamp()
    out = []
    for c in contests:
        start = c.get("startTime")
        if not start or int(start) < now:
            continue
        slug = c.get("titleSlug", "")
        out.append(Contest(
            platform="LeetCode",
            name=c.get("title", ""),
            start_time=datetime.fromtimestamp(int(start), tz=timezone.utc),
            duration_minutes=int(c.get("duration", 0)) // 60,
            url=CONTEST_URL.format(slug=slug),
            id=slug,
        ))
    out.sort(key=lambda c: c.start_time)
    return out


QUERY = """query cpTrackerProfile($username: String!) {
  userContestRanking(username: $username) {
    rating
    globalRanking
    topPercentage
    attendedContestsCount
  }
  userContestRankingHistory(username: $username) {
    attended
    rating
    ranking
    contest { title startTime }
  }
  matchedUser(username: $username) {
    profile { ranking realName }
    submitStats {
      acSubmissionNum { difficulty count }
    }
  }
}"""


def user_stats(handle: str) -> UserStats:
    try:
        payload = http_post_json(
            GQL,
            {"query": QUERY, "variables": {"username": handle}},
            headers={"Referer": "https://leetcode.com/"},
        )
    except FetchError as exc:
        return UserStats(platform="LeetCode", handle=handle, ok=False,
                         error=str(exc))

    data = payload.get("data", {})
    matched = data.get("matchedUser")
    if not matched:
        return UserStats(platform="LeetCode", handle=handle, ok=False,
                         error="handle not found")

    ranking = data.get("userContestRanking") or {}
    history_nodes = data.get("userContestRankingHistory") or []

    history: list[RatingPoint] = []
    results: list[ContestResult] = []
    last_rating = None
    for h in history_nodes:
        if not h or not h.get("attended"):
            continue
        contest = h.get("contest") or {}
        t = datetime.fromtimestamp(int(contest.get("startTime", 0)),
                                   tz=timezone.utc)
        rating = round(h.get("rating") or 0)
        history.append(RatingPoint(t, rating))
        delta = rating - last_rating if last_rating is not None else 0
        results.append(ContestResult(t, contest.get("title", ""),
                                     h.get("ranking") or 0, delta))
        last_rating = rating

    solved = {}
    for s in (matched.get("submitStats") or {}).get("acSubmissionNum", []):
        solved[s["difficulty"]] = s["count"]

    rating = ranking.get("rating")
    return UserStats(
        platform="LeetCode",
        handle=handle,
        ok=True,
        rating=round(rating) if rating else None,
        rank=(f"Top {ranking.get('topPercentage')}%" if ranking.get("topPercentage") else None),
        global_rank=ranking.get("globalRanking"),
        top_percentage=ranking.get("topPercentage"),
        contests_attended=ranking.get("attendedContestsCount"),
        solved=solved,
        history=history,
        results=results,
        extra={
            "real_name": (matched.get("profile") or {}).get("realName"),
            "leetcoderank": (matched.get("profile") or {}).get("ranking"),
        },
    )