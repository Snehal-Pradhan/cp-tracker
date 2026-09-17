"""Screens: dashboard, per-platform detail and settings modal."""

from __future__ import annotations

from datetime import datetime

from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import ModalScreen, Screen
from textual.widgets import (Button, DataTable, Footer, Header, Input,
                             Label, Sparkline, Static)

from .. import config
from ..models import Contest, Store, UserStats
from .format import (PLATFORM_COLORS, dur_mins, fmt_time, in_when)
from .widgets import PlatformCard, StatTile

PLATFORM_ORDER = ["codeforces", "leetcode", "codechef"]


def rating_color(rating):
    if rating is None:
        return "default"
    if rating >= 2400:
        return "red"
    if rating >= 2200:
        return "orange"
    if rating >= 1900:
        return "magenta"
    if rating >= 1600:
        return "blue"
    if rating >= 1400:
        return "cyan"
    if rating >= 1200:
        return "green"
    return "gray"


class Dashboard(Screen):
    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("r", "refresh", "Refresh"),
        Binding("c", "configure", "Config"),
        Binding("enter", "open", "Detail"),
        Binding("tab", "focus_next", "Next"),
    ]

    def __init__(self, **kw):
        super().__init__(**kw)
        self.cards: list[PlatformCard] = []

    def compose(self) -> ComposeResult:
        cfg = config.load_config()
        yield Header(show_clock=True)
        with Horizontal(id="body"):
            with Vertical(id="contest-col"):
                yield Static("[b]Upcoming contests[/]", classes="section-title")
                yield DataTable(id="contest-table", cursor_type="row",
                                zebra_stripes=True)
                yield Static("", id="status", classes="status")
            with VerticalScroll(id="cards-col"):
                for key in PLATFORM_ORDER:
                    label = config.PLATFORM_LABEL[key]
                    card = PlatformCard(key, label, cfg.get(key, ""))
                    self.cards.append(card)
                    yield card
        yield Footer()

    def on_mount(self):
        table = self.query_one("#contest-table", DataTable)
        table.auto_width = False
        table.add_column("Platform", key="plat", width=11)
        table.add_column("When", key="when", width=10)
        table.add_column("Starts", key="start", width=15)
        table.add_column("Contest", key="name", width=28)

        for key in PLATFORM_ORDER:
            cached = config.load_cache().get(key, {}).get("data")
            if cached:
                try:
                    self.app.store.stats[key] = UserStats.from_dict(cached)
                except Exception:  # noqa: BLE001
                    pass
        cached_contests = config.load_cache().get("contests", {}).get("data")
        if cached_contests:
            try:
                self.app.store.contests = [Contest.from_dict(d)
                                           for d in cached_contests]
            except Exception:  # noqa: BLE001
                pass

        self.apply_store()
        self.app.refresh_async()

    def on_screen_resume(self):
        self.apply_store()

    def apply_store(self):
        store: Store = self.app.store
        cfg = config.load_config()
        for card in self.cards:
            card.handle = cfg.get(card.key, "")
            card.stats = store.stat_for(card.key)
            card.render_content()
        self._render_contests(store.contests)
        if store.last_updated:
            label = (f"[dim]updated[/] "
                     f"{datetime.fromtimestamp(store.last_updated):%H:%M:%S}")
            self.query_one("#status", Static).update(label)
        else:
            self.query_one("#status", Static).update("[dim]refreshing…[/]")

    def _render_contests(self, contests: list[Contest]):
        table = self.query_one("#contest-table", DataTable)
        table.clear()
        now = datetime.now().timestamp()
        upcoming = [c for c in contests if c.start_time.timestamp() > now]
        if not upcoming:
            table.add_row("[dim]—[/]", "[dim]—[/]", "[dim]—[/]",
                          "[dim]no upcoming contests[/]")
            return
        for c in upcoming[:15]:
            color = PLATFORM_COLORS.get(c.platform, "default")
            table.add_row(f"[{color}]{c.platform}[/]", in_when(c.start_time),
                          fmt_time(c.start_time), c.name)

    def action_quit(self):
        self.app.exit()

    def action_configure(self):
        self.app.push_screen(SetupModal())

    def action_refresh(self):
        self.query_one("#status", Static).update("[dim]refreshing…[/]")
        self.app.refresh_async()

    def action_open(self):
        card = self.focused
        if isinstance(card, PlatformCard):
            self.app.open_platform(card.key)


class PlatformScreen(Screen):
    BINDINGS = [
        Binding("q", "back", "Back"),
        Binding("escape", "back", "Back"),
        Binding("r", "refresh", "Refresh"),
    ]

    def __init__(self, key: str, **kw):
        super().__init__(**kw)
        self.key = key
        self.label = config.PLATFORM_LABEL.get(key, key)
        self.tiles: dict[str, StatTile] = {}

    def compose(self) -> ComposeResult:
        color = PLATFORM_COLORS.get(self.label, "default")
        yield Header(show_clock=True)
        with VerticalScroll(id="detail"):
            yield Static(f"[bold {color}]{self.label}[/]",
                         classes="detail-title", id="detail-title")
            yield Label("", id="detail-sub")
            with Horizontal(id="tiles"):
                self.tiles["rating"] = StatTile("Rating", accent=color)
                self.tiles["max"] = StatTile("Max / Highest")
                self.tiles["rank"] = StatTile("Rank")
                self.tiles["attended"] = StatTile("Contests")
                for t in (self.tiles["rating"], self.tiles["max"],
                          self.tiles["rank"], self.tiles["attended"]):
                    yield t
            yield Static("", id="extra-line", classes="extra-line")
            yield Static("[b]Rating trend[/]", classes="section-title")
            with Vertical(id="plot"):
                yield Sparkline([], classes="big-spark", id="detail-spark")
                yield Static("", id="plot-range", classes="plot-range")
            yield Static("[b]Recent contests[/]", classes="section-title")
            yield DataTable(id="recent-table", cursor_type="row",
                            zebra_stripes=True)
            yield Static("[b]Upcoming contests[/]", classes="section-title")
            yield DataTable(id="up-table", cursor_type="row",
                            zebra_stripes=True)
        yield Footer()

    def on_mount(self):
        self.query_one("#recent-table", DataTable).add_columns(
            "Date", "Contest", "Rank", "Δ")
        self.query_one("#up-table", DataTable).add_columns(
            "When", "Start (local)", "Dur", "Contest")
        self.apply_store()

    def on_screen_resume(self):
        self.apply_store()

    def apply_store(self):
        store: Store = self.app.store
        cfg = config.load_config()
        handle = cfg.get(self.key, "")
        color = PLATFORM_COLORS.get(self.label, "default")
        self.query_one("#detail-title", Static).update(
            f"[bold {color}]{self.label}[/]  [dim]@{handle}[/]")
        stats = store.stat_for(self.key)

        if stats is None:
            self.query_one("#detail-sub", Label).update("waiting for data…")
            return

        if not stats.ok:
            self.query_one("#detail-sub", Label).update(
                f"[red]{stats.error}[/]")
            for name, t in self.tiles.items():
                t.set_value("—")
            return

        self.query_one("#detail-sub", Label).update(
            f"[dim]last updated "
            f"{datetime.fromtimestamp(store.last_updated or 0):%H:%M:%S}[/]"
            if store.last_updated else "[dim]—[/]")

        rc = rating_color(stats.rating)
        self.tiles["rating"].set_value(
            f"[{rc}]{stats.rating}[/]" if stats.rating is not None else "—")
        self.tiles["max"].set_value(
            str(stats.max_rating) if stats.max_rating is not None else "—")
        rank = stats.rank or (f"#{stats.global_rank:,}"
                              if stats.global_rank else "—")
        self.tiles["rank"].set_value(rank)
        self.tiles["attended"].set_value(
            str(stats.contests_attended) if stats.contests_attended
            else "—")

        extra_line = []
        if self.label == "LeetCode" and stats.solved:
            solve = stats.solved
            extra_line.append(f"Solved: E[green]{solve.get('Easy', 0)}[/] "
                              f"M[orange]{solve.get('Medium', 0)}[/] "
                              f"H[red]{solve.get('Hard', 0)}[/] "
                              f"([b]{solve.get('All', 0)}[/] total)")
        if stats.extra.get("country"):
            extra_line.append(f"[dim]country[/] {stats.extra['country']}")
        if stats.extra.get("organization"):
            extra_line.append(f"[dim]org[/] {stats.extra['organization']}")
        self.query_one("#extra-line", Static).update("   ·   ".join(extra_line))

        pts = [p.rating for p in stats.history]
        spark = self.query_one("#detail-spark", Sparkline)
        if len(pts) >= 2:
            spark.data = pts
            self.query_one("#plot-range", Static).update(
                f"[dim]low[/] {min(pts)}   {len(pts)} contests   "
                f"[dim]high[/] {max(pts)}")
        else:
            spark.data = []
            self.query_one("#plot-range", Static).update(
                "[dim]not enough contest history yet[/]")

        self._render_recent(stats)
        self._render_upcoming()

    def _render_recent(self, stats: UserStats):
        table = self.query_one("#recent-table", DataTable)
        table.clear()
        if self.label == "CodeChef":
            table.add_row("[dim]—[/]", "[dim]CodeChef does not expose rating"
                                     " history via a public API; custom "
                                     "solutions are required.[/]")
            return
        results = stats.results[-12:]
        results.reverse()
        for r in results:
            delta = f"[{'green' if r.delta >= 0 else 'red'}]{r.delta:+d}[/]"
            table.add_row(r.date.strftime("%Y-%m-%d"), r.name,
                          str(r.rank), delta)

    def _render_upcoming(self):
        store: Store = self.app.store
        table = self.query_one("#up-table", DataTable)
        table.clear()
        now = datetime.now().timestamp()
        mine = [c for c in store.contests
                if c.platform == self.label and c.start_time.timestamp() > now]
        if not mine:
            table.add_row("[dim]—[/]", "[dim]—[/]", "[dim]—[/]",
                          "[dim]no upcoming contests[/]")
            return
        for c in mine[:12]:
            table.add_row(in_when(c.start_time), fmt_time(c.start_time),
                          dur_mins(c.duration_minutes), c.name)

    def action_back(self):
        self.app.pop_screen()

    def action_refresh(self):
        self.app.refresh_async()


class SetupModal(ModalScreen):
    BINDINGS = [Binding("escape", "cancel", "Cancel")]

    def __init__(self, focus_key: str | None = None, **kw):
        super().__init__(**kw)
        self.focus_key = focus_key

    def compose(self) -> ComposeResult:
        cfg = config.load_config()
        with Vertical(id="setup-box"):
            yield Static("[b]Configure your handles[/]", id="setup-title")
            yield Label("Add your competitive programming handles. "
                        "Values are stored locally.", id="setup-hint")
            yield Input(cfg.get("codeforces", ""), placeholder="Codeforces "
                        "handle (e.g. tourist)", id="in-cf",
                        classes="setup-input")
            yield Input(cfg.get("leetcode", ""), placeholder="LeetCode "
                        "handle (e.g. wangzi6147)", id="in-lc",
                        classes="setup-input")
            yield Input(cfg.get("codechef", ""), placeholder="CodeChef "
                        "handle (e.g. gennady.korotkevich)", id="in-cc",
                        classes="setup-input")
            with Horizontal(id="setup-buttons"):
                yield Button("Save", id="save", variant="primary")
                yield Button("Cancel", id="cancel")

    def on_mount(self):
        mapping = {"codeforces": "cf", "leetcode": "lc", "codechef": "cc"}
        if self.focus_key:
            nxt = self.get_child_by_id(f"in-{mapping.get(self.focus_key)}")
            self.set_focus(nxt)

    @on(Button.Pressed, "#save")
    def _save(self, _event):
        cfg = config.save_config({
            "codeforces": self.query_one("#in-cf", Input).value.strip(),
            "leetcode": self.query_one("#in-lc", Input).value.strip(),
            "codechef": self.query_one("#in-cc", Input).value.strip(),
        })
        self.app.refresh_async()
        self.dismiss(cfg)

    @on(Button.Pressed, "#cancel")
    def _cancel(self, _event):
        self.dismiss()

    def action_cancel(self):
        self.dismiss()
