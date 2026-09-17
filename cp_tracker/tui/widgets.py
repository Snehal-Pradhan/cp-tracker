"""Reusable TUI widgets."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Sparkline, Static

from ..models import UserStats

PLATFORM_ICONS = {"Codeforces": "CF", "LeetCode": "LC", "CodeChef": "CC"}

ACCENT_HEX = "#b8aa4a"
BAR_EMPTY_HEX = "#2a2f38"
MAX_STARS = 7


def stars_label(count: int | None) -> str:
    """Plain textual star level (e.g. '3 Star'), no glyphs."""
    count = int(count or 0)
    return "—" if count <= 0 else f"{count} Star"


def cc_progress_bar(count: int | None, width: int = 14) -> str:
    """A plain coloured progress bar for the CodeChef card graph slot."""
    count = int(count or 0)
    filled = round(min(count, MAX_STARS) / MAX_STARS * width)
    return (f"[{ACCENT_HEX}]" + "\u2588" * filled + "[/]"
            f"[{BAR_EMPTY_HEX}]" + "\u2588" * (width - filled) + "[/]")


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
        yield Static("", classes="cc-bar", id=f"starmeter-{self.key}")
        yield Static("", classes="chips", id=f"chips-{self.key}")

    def _show_chart(self, use_meter: bool, meter_text: str = ""):
        spark = self.query_one(f"#spark-{self.key}", Sparkline)
        meter = self.query_one(f"#starmeter-{self.key}", Static)
        spark.display = not use_meter
        meter.display = use_meter
        if use_meter:
            meter.update(meter_text)

    def render_content(self):
        stats = self.stats
        icon = PLATFORM_ICONS[self.label]

        self.query_one(f"#badge-{self.key}", Static).update(
            f"[bold]{icon}[/]")
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
            self.query_one(f"#rating-{self.key}", Static).update(
                f"[bold]{rating}[/]")
        else:
            self.query_one(f"#rating-{self.key}", Static).update("[dim]unrated[/]")

        rank_txt = stats.rank or (
            f"#{stats.global_rank:,}" if stats.global_rank else "—")
        caption = "CURRENT RATING"
        if self.key == "codechef":
            stars = stats.extra.get("stars") or 0
            rank_txt = stars_label(stars)
            caption = "STAR LEVEL"
        self.query_one(f"#cap-{self.key}", Static).update(caption)
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

        if self.key == "codechef":
            stars = stats.extra.get("stars") or 0
            if stars:
                self._show_chart(True, cc_progress_bar(stars))
            else:
                self._show_chart(True, "[dim]no rating yet[/]")
        else:
            self._show_chart(False)
            self.query_one(f"#spark-{self.key}", Sparkline).data = pts

        self.query_one(f"#chips-{self.key}", Static).update(
            "  ·  ".join(chips) if chips else "")

    def _set(self, rating="", caption="", rank="", chips="", *, error: bool = False):
        self.query_one(f"#rating-{self.key}", Static).update(
            rating or "[dim]·[/]")
        self.query_one(f"#cap-{self.key}", Static).update(caption)
        style = "red" if error else "dim"
        self.query_one(f"#rank-{self.key}", Static).update(
            f"[{style}]{rank}[/]")
        self.query_one(f"#chips-{self.key}", Static).update(chips)
        self.query_one(f"#spark-{self.key}", Sparkline).data = []
        self._show_chart(False)
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