"""Textual screen (R11): the summary on top, three tabs (problem rows · by code · clean rows), [/] filter, [e] export.
The screen only shows what the engine (checks) already decided."""
from __future__ import annotations

from pathlib import Path

from textual.app import App, ComposeResult
from textual.widgets import DataTable, Footer, Header, Input, Static, TabbedContent, TabPane

from . import checks


class CheckApp(App):
    TITLE = "tcheck"
    BINDINGS = [("slash", "filter", "Filter"), ("e", "export", "Export clean rows"), ("escape", "clear", "Clear filter"),
                ("q", "quit", "Quit")]
    CSS = "#top { height: auto; margin: 0 1; }"

    def __init__(self, args, rows: list, schema: dict, result: dict):
        super().__init__()
        self.args, self.rows, self.schema, self.result = args, rows, schema, result
        self.word = ""
        self.exported = ""

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static("", id="top", markup=False)
        yield Input(placeholder="filter: key or code, Enter to apply, Esc to clear", id="filter")
        with TabbedContent(id="tabs"):
            with TabPane("Problem rows", id="problems"):
                yield DataTable(id="problem-table", cursor_type="row")
            with TabPane("By code", id="codes"):
                yield DataTable(id="code-table", cursor_type="row")
            with TabPane("Clean rows", id="clean"):
                yield DataTable(id="clean-table", cursor_type="row")
        yield Footer()

    def on_mount(self):
        self.query_one("#filter", Input).display = False
        r = self.result
        self.sub_title = f"{self.args.file} · schema {r['schema']}"
        self.query_one("#top", Static).update(
            f"{r['batch']} · {r['total']} rows · valid {r['valid']} · invalid {r['invalid']} · score {checks.score(r)}")
        self.fill()

    def keep(self, row: dict) -> bool:
        return not self.word or self.word in row["key"] or any(self.word in e for e in row["errors"])

    def fill(self):
        problems = self.query_one("#problem-table", DataTable)
        problems.clear(columns=True)
        problems.add_columns("row", "key", "errors")
        for row in self.result["rows"]:
            if not row["ok"] and self.keep(row):
                problems.add_row(str(row["row"]), row["key"] or "-", ", ".join(row["errors"]))
        codes = self.query_one("#code-table", DataTable)
        codes.clear(columns=True)
        codes.add_columns("count", "code", "rows")
        for code, count in sorted(self.result["codes"].items(), key=lambda kv: (-kv[1], kv[0])):
            if not self.word or self.word in code:
                where = [str(r["row"]) for r in self.result["rows"] if code in r["errors"]]
                codes.add_row(str(count), code, " ".join(where))
        clean = self.query_one("#clean-table", DataTable)
        clean.clear(columns=True)
        clean.add_columns("row", "key")
        for row in self.result["rows"]:
            if row["ok"] and self.keep(row):
                clean.add_row(str(row["row"]), row["key"] or "-")

    def action_filter(self):
        box = self.query_one("#filter", Input)
        box.value, box.display = "", True
        self.call_after_refresh(box.focus)

    def on_input_submitted(self, event: Input.Submitted):
        self.word = event.value.strip().lstrip("/").strip()     # the "/" that opened the box may land in it
        event.input.display = False
        self.fill()
        self.query_one("#problem-table", DataTable).focus()

    def action_clear(self):
        self.word = ""
        box = self.query_one("#filter", Input)
        box.value, box.display = "", False
        self.fill()
        self.query_one("#problem-table", DataTable).focus()

    def action_export(self):
        from .cli import write_rows

        source = Path(self.args.file)
        target = self.args.out or str(source.with_suffix(".clean" + (".csv" if source.suffix.lower() == ".csv" else ".json")))
        clean, _ = checks.split(self.rows, self.result)
        write_rows(target, clean)
        self.exported = target
        self.notify(f"{len(clean)} clean rows → {target}")
