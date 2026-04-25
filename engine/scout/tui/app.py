"""Scout TUI — Terminal UI for managing action items.

Run with: scoutctl tui
Or: textual run scout/tui/app.py
"""

from textual.app import App

from scout.tui.screens.dashboard import DashboardScreen


class ScoutApp(App):
    """The main Scout TUI application."""

    TITLE = "SCOUT Action Items"
    CSS = """
    Screen {
        background: $surface;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("r", "refresh", "Refresh"),
    ]

    def on_mount(self) -> None:
        self.push_screen(DashboardScreen())

    def action_refresh(self) -> None:
        """Reload action items from disk."""
        screen = self.screen
        if isinstance(screen, DashboardScreen):
            screen.refresh_items()
