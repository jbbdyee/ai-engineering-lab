"""Textual screen (R11): targets ranked by failed tries on the left, the runs of the chosen target on the right."""
from __future__ import annotations

from pathlib import Path

from textual.app import App, ComposeResult
from textual.containers import Horizontal
from textual.widgets import DataTable, Footer, Header, Static

from . import log


class LogApp(App):
    TITLE = "tretry"
    BINDINGS = [("r", "reload", "Reload"), ("f", "failed_only", "Failed only"), ("q", "quit", "Quit")]
    CSS = "#targets { width: 55%; } #tries { width: 45%; } #note { height: auto; margin: 0 1; }"

    def __init__(self, path: Path):
        super().__init__()
        self.path = Path(path)
        self.rows: list[dict] = []
        self.failed_only = False
        self.chosen: str | None = None

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal():
            yield DataTable(id="targets", cursor_type="row")
            yield DataTable(id="tries", cursor_type="row")
        yield Static("", id="note", markup=False)
        yield Footer()

    def on_mount(self):
        self.sub_title = str(self.path)
        self.action_reload()

    def action_reload(self):
        self.rows = log.read(self.path)
        table = self.query_one("#targets", DataTable)
        table.clear(columns=True)
        table.add_columns("target", "runs", "ok%", "tries/run", "failed", "fallback", "p95 s")
        for r in log.stats(self.rows):
            table.add_row(r["target"][:60], r["runs"], f"{r['success_rate'] * 100:.0f}%", r["attempts_per_run"],
                          r["failed_attempts"], r["fallbacks"], f"{r['p95_seconds']:.2f}", key=r["target"])
        total = len(log.runs(self.rows))
        self.query_one("#note", Static).update(f"{total} run(s) · {len(self.rows)} tr(ies) in {self.path} · "
                                               "[enter] show tries · [f] failed only · [r] reload")
        if self.chosen is None and table.row_count:
            self.chosen = str(table.coordinate_to_cell_key((0, 0)).row_key.value)
        self.show_tries()

    def action_failed_only(self):
        self.failed_only = not self.failed_only
        self.show_tries()

    def on_data_table_row_highlighted(self, event: DataTable.RowHighlighted):
        if event.data_table.id == "targets" and event.row_key is not None:
            self.chosen = str(event.row_key.value)
            self.show_tries()

    def show_tries(self):
        table = self.query_one("#tries", DataTable)
        table.clear(columns=True)
        table.add_columns("run", "try", "at +s", "result", "error", "s")
        for number, group in enumerate(log.runs(self.rows), 1):
            if group[-1]["target"] != self.chosen:
                continue
            for r in group:
                if self.failed_only and r["ok"]:
                    continue
                table.add_row(number, "fallback" if r.get("fallback") else r["attempt"], f"{r['started']:.2f}",
                              "✔" if r["ok"] else "✘", (r.get("error") or "")[:40], f"{r['seconds']:.2f}")
