"""Reusable TUI widgets."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Sparkline, Static

from ..models import UserStats
from .format import PLATFORM_COLORS

PLATFORM_ICONS = {"Codeforces": "CF", "LeetCode": "LC", "CodeChef": "CC"}

PLATFORM_HEX = {
    "Codeforces": "#d4394b",
    "LeetCode": "#ffa116",
    "CodeChef": "#58a83b",
}

RATING_COLORS = [
    (2400, "#dc2626"),
    (2200, "#ea580c"),
    (1900, "#a855f7"),
    (1600, "#3b82f6"),
    (1400, "#06b6d4"),
    (1200, "#22c55e"),
]


def rating_hex(rating):
    if rating is None:
        return "default"
    for threshold, color in RATING_COLORS:
        if rating >= threshold:
            return color
    return "#9ca3af"


class PlatformCard(Vertical, can_focus=True):
    """A focusable summary card for one platform."""

    def __init__(self, key: str, label: str, handle: str = "",
                 stats: UserStats | None = None, **kw):
        super().__init__(**kw)
        self.key = key
        self.label = label
        self.handle = handle
        self.stats = stats
        self.add_class("platform-card")
        self.add_class(f"plat-{self.key}")

    def compose(self) -> ComposeResult:
        with Horizontal(classes="head-row"):
            yield Static("", classes="badge", id=f"badge-{self.key}")
            yield Static("", classes="pname", id=f"pname-{self.key}")
            yield Static("", classes="phandle", id=f"phandle-{self.key}")
        with Horizontal(classes="body-row"):
            yield Static("", classes="rating", id=f"rating-{self.key}")
            with Vertical(classes="side"):
                yield Static("", classes="caption", id=f"cap-{self.key}")
                yield Static("", classes="rank", id=f"rank-{self.key}")
        yield Sparkline([], classes="card-spark", id=f"spark-{self.key}")
        yield Static("", classes="chips", id=f"chips-{self.key}")

    def render_content(self):
        stats = self.stats
        hexc = PLATFORM_HEX.get(self.label, "#ffffff")
        icon = PLATFORM_ICONS[self.label]

        self.query_one(f"#badge-{self.key}", Static).update(
            f"[bold on {hexc} #1e1e1e] {icon} [/]")
        self.query_one(f"#pname-{self.key}", Static).update(
            f"[bold]{self.label}[/]")
        self.query_one(f"#phandle-{self.key}", Static).update(
            f"[dim]@{self.handle or '—'}[/]")

        if stats is None:
            self._set("", "LOADING", "fetching data …", "")
            return
        if not stats.ok:
            self._set("", "STATUS", stats.error or "error",
                      "press [b]r[/] retry · press [b]c[/] configure",
                      error=True)
            return

        pts = [p.rating for p in stats.history][-40:]
        rating = stats.rating
        if rating is not None:
            rc = rating_hex(rating)
            self.query_one(f"#rating-{self.key}", Static).update(
                f"[bold {rc}]{rating}[/]")
        else:
            self.query_one(f"#rating-{self.key}", Static).update("[dim]unrated[/]")

        rank_txt = stats.rank or (
            f"#{stats.global_rank:,}" if stats.global_rank else "—")
        self.query_one(f"#cap-{self.key}", Static).update("CURRENT RATING")
        self.query_one(f"#rank-{self.key}", Static).update(f"{rank_txt}")

        chips = []
        if stats.global_rank:
            chips.append(f"[dim]global[/] #{stats.global_rank:,}")
        if stats.max_rating:
            chips.append(f"[dim]max[/] {stats.max_rating}")
        if stats.contests_attended:
            chips.append(f"[dim]contests[/] {stats.contests_attended}")
        if stats.top_percentage is not None:
            chips.append(f"[dim]top[/] {stats.top_percentage:g}%")
        if chips:
            self.query_one(f"#chips-{self.key}", Static).update(
                "  ·  ".join(chips))
        else:
            self.query_one(f"#chips-{self.key}", Static).update("")
        self.query_one(f"#spark-{self.key}", Sparkline).data = pts

    def _set(self, rating="", caption="", rank="", chips="", *, error: bool = False):
        self.query_one(f"#rating-{self.key}", Static).update(
            rating or "[dim]·[/]")
        self.query_one(f"#cap-{self.key}", Static).update(caption)
        style = "red" if error else "dim"
        self.query_one(f"#rank-{self.key}", Static).update(
            f"[{style}]{rank}[/]")
        self.query_one(f"#chips-{self.key}", Static).update(chips)
        self.query_one(f"#spark-{self.key}", Sparkline).data = []
        if error:
            self.add_class("card-error")

    def on_mount(self):
        self.render_content()

    def on_click(self):
        self.focus()
        self.action_select()

    def action_select(self):
        app = self.app
        target = getattr(app, "open_platform", None)
        if target:
            target(self.key)


class StatTile(Vertical):
    """A small labelled value tile used on detail screens."""

    def __init__(self, label: str, value: str = "—", accent: str | None = None,
                 **kw):
        super().__init__(**kw)
        self._label = label
        self._value = value
        self._accent = accent
        self.classes = "stat-tile"

    def compose(self) -> ComposeResult:
        yield Static(self._label, classes="stat-label")
        yield Static(self._value, classes="stat-value")

    def set_value(self, value: str, accent: str | None = None):
        self._value = value
        self._accent = accent
        self.query_one(".stat-value", Static).update(value)


def tile(label: str, value) -> StatTile:
    return StatTile(label, value)