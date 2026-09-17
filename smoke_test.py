import asyncio
import sys
from datetime import datetime, timedelta, timezone

sys.path.insert(0, "/Users/sp/Desktop/cp")

import cp_tracker.network as network
from cp_tracker import config
from cp_tracker.models import Contest, ContestResult, RatingPoint, UserStats

config.save_config({"codeforces": "tourist", "leetcode": "wangzi6147",
                    "codechef": "gennady.korotkevich"})


def make_stats(platform, rating, rank, attended, history, results):
    return UserStats(platform=platform, handle="handle", ok=True,
                     rating=rating, max_rating=rating + 100, rank=rank,
                     global_rank=123, contests_attended=attended,
                     solved={"Easy": 10, "Medium": 20, "Hard": 5},
                     history=history, results=results)


def make_history(n, start):
    pts = []
    r = 1400
    for i in range(n):
        r += i * 13 % 40 - 18
        pts.append(RatingPoint(start + timedelta(days=i * 7), max(800, r)))
    return pts


now = datetime.now(timezone.utc)
h = make_history(20, now - timedelta(days=200))
res = [ContestResult(now - timedelta(days=d), f"Round {i}",
                     i * 13, 11) for i, d in enumerate(range(14, 0, -1))]
NETWORK = {
    "codeforces": make_stats("Codeforces", 2100, "Candidate Master", 30, h, res),
    "leetcode": make_stats("LeetCode", 1800, "Top 2%", 25, h, res),
    "codechef": make_stats("CodeChef", 1750, "\u2605\u2605\u2605", None, [], []),
}
NETWORK["codechef"].extra["stars"] = 3
network.refresh_stats = lambda: NETWORK
network.refresh_contests = lambda: [
    Contest("Codeforces", "CF Round", now + timedelta(days=2), 150, "http://x", "1"),
    Contest("LeetCode", "Weekly 1", now + timedelta(days=1), 90, "http://y", "2"),
    Contest("CodeChef", "Starters", now + timedelta(days=3), 180, "http://z", "3"),
]

from cp_tracker.tui.app import CPApp
from cp_tracker.tui.screens import Dashboard, PlatformScreen, SetupModal
from cp_tracker.tui.widgets import PlatformCard


async def main():
    app = CPApp()
    async with app.run_test(size=(120, 36)) as pilot:
        await pilot.pause()
        assert isinstance(app.screen, Dashboard), app.screen
        assert len(app.screen.cards) == 3
        print("dashboard ok, cards:", [c.key for c in app.screen.cards])

        sw = app.screen.query_one("#status", object)
        print("status widget:", sw.__class__.__name__)

        app.screen.cards[0].focus()
        await pilot.press("enter")
        await pilot.pause()
        assert isinstance(app.screen, PlatformScreen)
        print("detail ok:", app.screen.label)

        await pilot.press("q")
        await pilot.pause()
        assert isinstance(app.screen, Dashboard)
        print("back ok")

        app.screen.cards[2].focus()
        await pilot.press("c")
        await pilot.pause()
        assert isinstance(app.screen, SetupModal)
        print("modal ok")

        await pilot.press("escape")
        await pilot.pause()
        assert isinstance(app.screen, Dashboard)

        await pilot.press("q")
        await pilot.pause()
    print("ALL OK")


asyncio.run(main())