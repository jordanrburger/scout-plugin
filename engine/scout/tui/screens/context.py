"""Context links panel — shows related URLs for an action item."""

from __future__ import annotations

from textual.screen import ModalScreen
from textual.widgets import Static


class ContextPanel(ModalScreen):
    """Shows context links (Linear, GitHub, Slack) for the selected action item."""

    def compose(self):
        yield Static("Context panel — implementation in next run", id="placeholder")
