"""Textual screen (R8): tabs Prompts · Usage · Compare for one or more folders. Reads only; never calls an API."""
from __future__ import annotations

import json
from pathlib import Path

from textual.app import App, ComposeResult
from textual.widgets import DataTable, Footer, Header, Static, TabbedContent, TabPane

from . import tokens
from .scan import scan
from .usage import collect
from .workflow import is_workflow, llm_steps, load

BARS = " ▁▂▃▄▅▆▇█"


def is_workflow_file(path: Path) -> bool:
    try:
        return is_workflow(json.loads(path.read_text(encoding="utf-8")))
    except (OSError, ValueError):
        return False


def bars(values: dict[str, float]) -> str:
    top = max(values.values(), default=0) or 1
    return "  ".join(f"{key} {BARS[round(value / top * 8)]}" for key, value in values.items())


class CostApp(App):
    TITLE = "tcost"
    BINDINGS = [("r", "reload", "Reload"), ("q", "quit", "Quit")]
    CSS = "#hours { height: auto; margin: 1 1; } #note { height: auto; margin: 0 1; }"

    def __init__(self, paths: str | list[str], prices):
        super().__init__()
        self.paths = [Path(p) for p in ([paths] if isinstance(paths, str) else paths)]
        self.prices = prices

    def compose(self) -> ComposeResult:
        yield Header()
        with TabbedContent(initial="prompts"):
            with TabPane("Prompts", id="prompts"):
                yield DataTable(id="prompt-table")
            with TabPane("Usage", id="usage"):
                yield Static("", id="usage-head")
                yield DataTable(id="usage-table")
                yield Static("", id="hours")
            with TabPane("Compare", id="compare"):
                yield DataTable(id="compare-table")
        yield Static("", id="note", markup=False)
        yield Footer()

    def on_mount(self):
        self.sub_title = f"{' '.join(map(str, self.paths))} · prices {self.prices.checked or '?'}"
        self.action_reload()

    def action_reload(self):
        texts, workflows, reports = [], [], []
        for path in self.paths:
            if path.is_dir():
                found = scan(path)
                texts, workflows, reports = texts + found.texts, workflows + found.workflows, reports + found.reports
            elif path.suffix == ".json":
                (workflows if is_workflow_file(path) else reports).append(path)
            else:
                texts.append(path)
        models = sorted(self.prices.models)
        rows: list[tuple[str, int, str]] = []
        for path in texts:
            rows.append((path.name, tokens.count(path.read_text(encoding="utf-8")), ""))
        for path in workflows:
            for step in llm_steps(load(path)):
                rows.append((f"{path.name} · {step.node}", step.system_tokens, step.model))
        table = self.query_one("#prompt-table", DataTable)
        table.clear(columns=True)
        table.add_columns("prompt", "tokens", *[f"{m} /1,000" for m in models])
        for name, n, _ in rows:
            table.add_row(name, n, *[f"${self.prices.cost(m, n) * 1000:.4f}" for m in models])
        usage = collect(reports)
        self.query_one("#usage-head", Static).update(
            f"{usage.reports} report(s) · {usage.requests} request(s) · ${usage.total['cost_usd']:.6f}"
            f" · avg ${usage.avg_usd:.6f} · skipped {usage.skipped}")
        table = self.query_one("#usage-table", DataTable)
        table.clear(columns=True)
        table.add_columns("by", "name", "calls", "in", "out", "cost")
        for title, data in (("model", usage.by_model), ("user", usage.by_user)):
            for key, row in sorted(data.items(), key=lambda kv: -kv[1]["cost_usd"]):
                table.add_row(title, key, row["calls"], row["prompt_tokens"], row["completion_tokens"], f"${row['cost_usd']:.6f}")
        self.query_one("#hours", Static).update("by hour  " + bars({k: v["cost_usd"] for k, v in sorted(usage.by_hour.items())}))
        table = self.query_one("#compare-table", DataTable)
        table.clear(columns=True)
        table.add_columns("prompt", "tokens", *[f"{m} /call (out 100)" for m in models])
        for name, n, _ in sorted(rows, key=lambda r: -r[1])[:10]:
            table.add_row(name, n, *[f"${self.prices.cost(m, n, 100):.6f}" for m in models])
        note = self.prices.warning()
        self.query_one("#note", Static).update(f"! {note}" if note else f"{len(rows)} prompt(s) · {len(reports)} report(s) · [r] reload")
