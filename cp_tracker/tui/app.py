"""CP Tracker Textual application."""

import time

from textual.app import App

from .. import config
from ..models import Store
from ..network import refresh_contests, refresh_stats
from .screens import Dashboard, PlatformScreen, SetupModal

CSS = """
$accent: #b8aa4a;
$background: #0c0d0f;
$surface: #121317;
$panel: #171a20;
$panel-lighten-1: #1e222b;
$panel-darken-1: #0f1014;
$boost: #1d2129;
$text: #c9cdd4;
$text-muted: #7f8691;
$text-disabled: #51575f;
$primary: #3d4552;
$secondary: #262b33;
$border: #2a2f38;
$success: #5aa469;
$warning: #c0a83f;
$error: #e06161;
$block-cursor-background: #2f353f;
$block-cursor-foreground: #e6e9ee;
$block-cursor-text-style: bold;
$block-cursor-blurred-background: #23272f;
$block-cursor-blurred-foreground: #c9cdd4;
$block-hover-background: #23272f;
$footer-background: #171a20;
$footer-foreground: #7f8691;
$footer-key-foreground: #c9cdd4;
$footer-key-background: #2a2f38;
$footer-description-foreground: #7f8691;
$scrollbar: #4a525c;
$scrollbar-hover: #59616d;
$scrollbar-active: #59616d;
$scrollbar-background: #1a1d22;
$scrollbar-background-hover: #1a1d22;
$scrollbar-background-active: #1a1d22;
$scrollbar-corner-color: transparent;

Screen {
    background: $surface;
}

* {
    scrollbar-size-vertical: 1;
    scrollbar-size-horizontal: 1;
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
    height: auto;
    border: round #2a2f38;
    background: $panel;
    padding: 0 2;
    margin: 0 0 1 0;
}

.platform-card:focus {
    border: round $accent;
}

.platform-card.card-error {
    border: round $error;
}

.head-row {
    height: 1;
    align-vertical: middle;
}

.badge {
    width: auto;
    height: 1;
    margin-right: 2;
    text-style: bold;
    color: $text-disabled;
}

.plat-codeforces .badge {
    color: #d4394b;
}

.plat-leetcode .badge {
    color: #ffa116;
}

.plat-codechef .badge {
    color: #58a83b;
}

.pname {
    width: 1fr;
    height: 1;
}

.phandle {
    width: auto;
    height: 1;
    color: $text-muted;
}

.body-row {
    height: 4;
    margin-top: 1;
}

.rating {
    width: 1fr;
    height: 4;
    content-align: left middle;
}

.side {
    width: 1fr;
    height: 4;
    align: left middle;
}

.caption {
    height: 1;
    color: $text-muted;
}

.rank {
    height: 2;
    text-style: bold;
}

.card-spark {
    height: 3;
}

.big-spark {
    height: 6;
}

Sparkline > .sparkline--max-color {
    color: #aab0b6;
}

Sparkline > .sparkline--min-color {
    color: #39404a;
}

.chips {
    height: 1;
    color: $text-muted;
    margin-bottom: 1;
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
    ENABLE_COMMAND_PALETTE = False

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
        if isinstance(screen, (Dashboard, PlatformScreen)):
            screen.apply_store()


def main():
    CPApp().run()


if __name__ == "__main__":
    main()