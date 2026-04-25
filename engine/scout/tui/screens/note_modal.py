"""Note input modal for adding notes to action items."""

from __future__ import annotations

from textual.screen import ModalScreen
from textual.widgets import Static


class NoteModal(ModalScreen):
    """Modal dialog for entering a note on an action item."""

    def compose(self):
        yield Static("Note modal — implementation in next run", id="placeholder")
