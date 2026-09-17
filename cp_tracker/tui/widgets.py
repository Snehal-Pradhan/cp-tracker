"""Reusable TUI widgets."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Sparkline, Static

from ..models import UserStats
from .format import PLATFORM_COLORS

PLATFORM_ICONS = {"Codeforces": "CF", "LeetCode": "LC", "CodeChef": "CC"}


class PlatformCard(Vertical, can_focus=True):
    """A focusable summary card for one platform."""

    def __init__(self, key: str, label: str, handle: str = "",
                 stats: UserStats | None = None, **kw):
        super().__init__(**kw)
        self.key = key
        self.label = label
        self.handle = handle
        self.stats = stats

    def compose(self) -> ComposeResult:
        yield Static(classes="card-title", id=f"title-{self.key}")
        yield Static(classes="card-rating", id=f"rating-{self.key}")
        yield Sparkline([0], classes="card-spark", id=f"spark-{self.key}")
        yield Static(classes="card-meta", id=f"meta-{self.key}")

    def render_content(self):
        stats = self.stats
        color = PLATFORM_COLORS.get(self.label, "default")
        title = self.query_one(f"#title-{self.key}", Static)

        if stats is None:
            title.update(f"[bold {color}]{PLATFORM_ICONS[self.label]} {self.label}[/]")
            self.query_one(f"#rating-{self.key}", Static).update(
                "[dim]waiting for data…[/]")
            self.query_one(f"#spark-{self.key}", Sparkline).data = []
            self.query_one(f"#meta-{self.key}", Static).update("")
            return

        if not stats.ok:
            title.update(f"[bold {color}]{PLATFORM_ICONS[self.label]} {self.label}[/]"
                         f"  [dim]@{self.handle or '?'}[/]")
            self.query_one(f"#rating-{self.key}", Static).update(
                f"[red]{stats.error}[/]" if stats.error else "[red]error[/]")
            self.query_one(f"#spark-{self.key}", Sparkline).data = []
            self.query_one(f"#meta-{self.key}", Static).update(
                "[dim]press r to retry, c to configure[/]")
            return

        handle_txt = f"[dim]@{self.handle}[/]" if self.handle else ""
        title.update(f"[bold {color}]{PLATFORM_ICONS[self.label]} {self.label}[/]  {handle_txt}")
        rating = stats.rating if stats.rating is not None else "—"
        self.query_one(f"#rating-{self.key}", Static).update(
            f"[bold]{rating}[/]")
        meta = []
        if stats.rank:
            meta.append(f"[{color}]{stats.rank}[/]")
        if stats.max_rating:
            meta.append(f"[dim]max[/] {stats.max_rating}")
        if stats.contests_attended:
            meta.append(f"[dim]contests[/] {stats.contests_attended}")
        if stats.global_rank:
            meta.append(f"[dim]global[/] #{stats.global_rank:,}")
        if not meta:
            meta.append("[dim]—[/]")
        self.query_one(f"#meta-{self.key}", Static).update("   ·   ".join(meta))

        pts = [p.rating for p in stats.history][-40:]
        self.query_one(f"#spark-{self.key}", Sparkline).data = pts

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
