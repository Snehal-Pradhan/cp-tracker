# CP Tracker

A terminal UI dashboard that tracks your competitive programming journey across
**Codeforces**, **LeetCode** and **CodeChef**.

## Features

- **Overview dashboard** — your current rating, rank, max rating and a rating
  trend sparkline for all three platforms on one screen, plus a combined list
  of upcoming contests.
- **Drill down per platform** — click (or press `Enter`) on a platform card to
  open a detail view:
  - **Codeforces**: rating trend, rating history / delta per contest, max
    rating, rank, country & org, upcoming CF contests.
  - **LeetCode**: contest rating, global rank, top %, solved breakdown by
    difficulty, contest history, upcoming contests.
  - **CodeChef**: rating, stars, highest rating, global / country rank
    (CodeChef does not expose rating history through a public API).
- **Setup modal** (`c`) to enter your handles for each platform.
- **Offline cache** — previously fetched data is shown instantly on startup,
  then refreshed in the background. Refresh anytime with `r`.

## Install

Requires Python 3.9+.

```bash
cd cp-tracker
python3 -m pip install -r requirements.txt
```

Optional: install as a command so you can run `cp-tracker` from anywhere:

```bash
python3 -m pip install -e .
```

## Run

```bash
python3 -m cp_tracker
```

Or if you installed the package:

```bash
cp-tracker
```

## Configure your handles

Press `c` inside the app, or edit `~/.cp_tracker/config.json` directly:

```json
{
  "codeforces": "tourist",
  "leetcode": "wangzi6147",
  "codechef": "gennady.korotkevich"
}
```

Data is cached in `~/.cp_tracker/cache.json` (Codeforces 15 min, LeetCode
30 min, CodeChef 60 min, contest lists 10 min).

## Keyboard

| Key       | Action                              |
| --------- | ----------------------------------- |
| `tab`     | move focus to the next widget       |
| `enter`   | open detail for the focused card    |
| `c`       | configure handles                   |
| `r`       | refresh all data from the APIs      |
| `q` / `esc` | quit or go back (on detail screens) |

Mouse works too: click a platform card to open its detail view.

## Notes on the data sources

- **Codeforces**: official API (`api.codeforces.com`).
- **LeetCode**: public GraphQL endpoint (`leetcode.com/graphql`).
- **CodeChef**: profile page scraping + the site's contest-list endpoint
  (there is no official public API). Global/country rank shows `Inactive` in
  the code if you are not on the current leaderboard.
- If a platform is temporarily down, the last cached data is used instead.