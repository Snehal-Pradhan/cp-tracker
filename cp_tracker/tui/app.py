"""CP Tracker Textual application."""

import time

from textual.app import App

from .. import config
from ..models import Store
from ..network import refresh_contests, refresh_stats
from .screens import Dashboard, PlatformScreen, SetupModal

CSS = """
Screen {
    background: $surface;
}

#body {
    height: 1fr;
}

#contest-col {
    width: 3fr;
    height: 1fr;
    border: round $primary;
    margin: 1 0 1 1;
    padding: 0 1;
}

#cards-col {
    width: 2fr;
    height: 1fr;
    margin: 1 1 1 0;
    padding: 0 1;
}

.section-title {
    height: 1;
    margin: 1 0;
    color: $text-muted;
}

.status {
    height: 1;
    margin-top: 1;
}

#contest-table {
    height: 1fr;
}

#contest-table, #recent-table, #up-table {
    border: none;
}

.platform-card {
    height: 9;
    border: round $border;
    background: $panel;
    padding: 0 1;
    margin: 0 0 1 0;
}

.platform-card:focus {
    border: round $accent;
    background: $boost;
}

.card-title {
    height: 1;
    margin-top: 1;
}

.card-rating {
    height: 2;
    margin: 0 0 0 1;
    content-align: left middle;
}

.card-rating Text {
    text-style: bold;
    color: $accent;
}

.card-spark {
    height: 3;
    color: $success;
}

.card-meta {
    height: 1;
    color: $text-muted;
}

/* ---- detail screen ---- */

#detail {
    height: 1fr;
    padding: 0 1;
}

.detail-title {
    height: 1;
    margin-top: 1;
}

#detail-sub {
    height: 1;
    margin-bottom: 1;
    color: $text-muted;
}

#tiles {
    height: 7;
    margin-bottom: 1;
}

.stat-tile {
    width: 1fr;
    height: 7;
    border: round $border;
    background: $panel;
    margin-right: 1;
    padding: 1;
}

.stat-label {
    color: $text-muted;
}

.stat-value {
    height: 2;
    text-style: bold;
    content-align: left middle;
}

.big-spark {
    height: 6;
    color: $accent;
}

#plot {
    border: round $border;
    background: $panel;
    margin-bottom: 1;
    padding: 0 1 1 1;
    height: auto;
}

.plot-range {
    height: 1;
    color: $text-muted;
}

#recent-table, #up-table {
    margin-bottom: 1;
}

/* ---- setup modal ---- */

#setup-box {
    width: 56;
    height: auto;
    border: round $accent;
    background: $surface;
    padding: 1 2;
    margin: 6 8;
}

#setup-title {
    height: 1;
    margin-bottom: 1;
}

#setup-hint {
    height: auto;
    margin-bottom: 1;
    color: $text-muted;
}

.setup-input {
    margin: 0 0 1 0;
}

#setup-buttons {
    height: 3;
    margin-top: 1;
    align-horizontal: right;
}

#setup-buttons Button {
    margin-right: 1;
}
"""


class CPApp(App):
    TITLE = "CP Tracker"
    SUB_TITLE = "your competitive programming journey"
    CSS = CSS

    def __init__(self, **kw):
        super().__init__(**kw)
        self.store = Store()

    def on_mount(self):
        self.push_screen(Dashboard())

    def open_platform(self, key: str):
        if not (config.load_config().get(key) or "").strip():
            self.push_screen(SetupModal())
            return
        self.push_screen(PlatformScreen(key))

    def refresh_async(self):
        return self.run_worker(self._refresh_worker, thread=True,
                               exclusive=True, name="refresh")

    def _refresh_worker(self):
        try:
            stats = refresh_stats()
            cons = refresh_contests()
        except Exception as exc:  # noqa: BLE001
            self.call_from_thread(self._deliver_error, str(exc))
            return
        self.call_from_thread(self._deliver, stats, cons)

    def _deliver(self, stats, cons):
        self.store.stats = stats
        self.store.contests = cons
        self.store.last_updated = time.time()
        self._apply_to_current()

    def _deliver_error(self, message):
        self._apply_to_current()
        self.notify(f"Refresh failed: {message}", severity="error")

    def _apply_to_current(self):
        screen = self.screen
        if isinstance(screen, Dashboard) or isinstance(screen, PlatformScreen):
            screen.apply_store()


def main():
    CPApp().run()


if __name__ == "__main__":
    main()