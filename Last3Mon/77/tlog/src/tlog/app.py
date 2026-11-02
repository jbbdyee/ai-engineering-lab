"""Textual screen (R11): the summary on top, groups on the left (failures · hours · slow runs, [t] to switch),
the runs of the chosen group on the right. The screen only calls the engine (load · metrics)."""
from __future__ import annotations

from collections import defaultdict

from textual.app import App, ComposeResult
from textual.containers import Horizontal
from textual.widgets import DataTable, Footer, Header, Static

from . import load, metrics

VIEWS = ("failures", "hours", "slow")


class LogApp(App):
    TITLE = "tlog"
    BINDINGS = [("t", "next_view", "Failures / hours / slow"), ("r", "reload", "Reload"), ("q", "quit", "Quit")]
    CSS = "#groups { width: 50%; } #runs { width: 50%; } #top { height: auto; margin: 0 1; }"

    def __init__(self, args):
        super().__init__()
        self.args = args
        self.rows: list[dict] = []
        self.view = "failures"
        self.groups: dict[str, list[dict]] = {}
        self.chosen: str | None = None

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static("", id="top", markup=False)
        with Horizontal():
            yield DataTable(id="groups", cursor_type="row")
            yield DataTable(id="runs", cursor_type="row")
        yield Footer()

    def on_mount(self):
        a = self.args
        self.sub_title = f"{a.url or a.file} · {a.date_from or '…'} ~ {a.date_to or '…'}"
        self.action_reload()

    def action_reload(self):
        a = self.args
        self.rows = load.read(a.file, a.url, a.date_from, a.date_to, a.tag, a.source)
        r = metrics.report(self.rows)
        self.query_one("#top", Static).update(
            f"{r['total']} runs · errors {r['errors']} ({metrics.percent(r['error_rate'])}) · p50 {r['p50_ms']}ms · "
            f"p95 {r['p95_ms']}ms · unanswered {metrics.percent(r['unanswered_rate'])} · SLO "
            + ("ok" if r["slo"]["ok"] else "breach " + ", ".join(r["slo"]["breaches"])))
        self.show_groups()

    def action_next_view(self):
        self.view = VIEWS[(VIEWS.index(self.view) + 1) % len(VIEWS)]
        self.chosen = None
        self.show_groups()

    def make_groups(self) -> list[tuple[str, list, list[dict]]]:
        """(key, cells for the left table, the runs of that group)."""
        if self.view == "failures":
            g: dict[tuple, list] = defaultdict(list)
            for row in self.rows:
                if row.get("status") == "error":
                    g[(row.get("error_node"), row.get("error_message"))].append(row)
            items = sorted(g.items(), key=lambda kv: -len(kv[1]))
            return [(f"{n}|{m}", [len(runs), n, str(m)[:40]], runs) for (n, m), runs in items]
        if self.view == "hours":
            g2: dict[str, list] = defaultdict(list)
            for row in self.rows:
                g2[str(row.get("started_at", ""))[:13]].append(row)
            out = []
            for hour in sorted(g2):
                runs = g2[hour]
                e = sum(1 for x in runs if x.get("status") == "error")
                out.append((hour, [hour, len(runs), e, metrics.percent(metrics.rate(e, len(runs)))], runs))
            return sorted(out, key=lambda item: (-item[1][2], item[0]))
        slow = sorted(self.rows, key=lambda x: -(x.get("duration_ms") or 0))[:20]
        return [(str(x.get("execution_id")), [x.get("duration_ms"), x.get("topic"), x.get("route") or "오류"], [x]) for x in slow]

    def show_groups(self):
        table = self.query_one("#groups", DataTable)
        table.clear(columns=True)
        table.add_columns(*{"failures": ("count", "node", "message"), "hours": ("hour", "runs", "errors", "rate"),
                            "slow": ("ms", "topic", "route")}[self.view])
        self.groups = {}
        for key, cells, runs in self.make_groups():
            self.groups[key] = runs
            table.add_row(*cells, key=key)
        if self.chosen not in self.groups:
            self.chosen = next(iter(self.groups), None)
        self.show_runs()

    def on_data_table_row_highlighted(self, event: DataTable.RowHighlighted):
        if event.data_table.id == "groups" and event.row_key is not None:
            self.chosen = str(event.row_key.value)
            self.show_runs()

    def show_runs(self):
        table = self.query_one("#runs", DataTable)
        table.clear(columns=True)
        table.add_columns("started_at", "status", "route", "ms", "topic", "question")
        for row in self.groups.get(self.chosen or "", []):
            table.add_row(row.get("started_at"), row.get("status"), row.get("route") or "오류", row.get("duration_ms"),
                          row.get("topic"), str(row.get("question"))[:24])
