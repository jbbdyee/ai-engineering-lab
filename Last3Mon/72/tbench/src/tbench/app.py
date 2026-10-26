"""Textual screen: sparkline and summary on top, one table row per call as it arrives."""
from pathlib import Path

from textual import work
from textual.app import App, ComposeResult
from textual.widgets import DataTable, Footer, Header, OptionList, Sparkline, Static
from textual.widgets.option_list import Option

from .runner import read_body, run
from .stats import fmt, summarize, summary_lines


class BenchApp(App):
    TITLE = "tbench"
    BINDINGS = [("q", "quit", "Quit")]
    CSS = """
    Sparkline { height: 4; margin: 0 1; }
    #summary { height: auto; margin: 0 1; }
    OptionList { height: 1fr; }
    """

    def __init__(self, settings, headers, pick=None):
        super().__init__()
        self.settings, self.headers, self.pick = settings, headers, pick
        self.results, self.body = [], None

    def compose(self) -> ComposeResult:
        yield Header()
        if self.pick:
            files = sorted(Path(self.pick).glob("*.json"))
            yield OptionList(*[Option(f.name, id=str(f)) for f in files], id="pick")
        yield Sparkline([], id="spark")
        yield Static("starting...", id="summary")
        yield DataTable(id="calls")
        yield Footer()

    def on_mount(self):
        table = self.query_one("#calls", DataTable)
        table.add_columns("#", "status", "seconds", "note")
        if self.pick:
            self.sub_title = f"choose a body from {self.pick}"
            self.query_one("#summary", Static).update("Enter: run with this body")
        else:
            self.start(self.settings.get("body_file"))

    def on_option_list_option_selected(self, event):
        event.option_list.remove()
        self.settings["body_file"] = event.option.id
        self.start(event.option.id)

    def start(self, body_file):
        s = self.settings
        self.body = read_body(body_file)
        self.sub_title = f"{s['method']} {s['url']}  body={Path(body_file).name if body_file else '-'}"
        self.measure()

    @work(thread=True, exclusive=True)
    def measure(self):
        s = self.settings
        for r in run(s["url"], self.body, s["n"], s["method"], self.headers, s["timeout"], s["warmup"], s["concurrency"]):
            self.call_from_thread(self.add_result, r)
        self.call_from_thread(self.finish)

    def add_result(self, r):
        self.results.append(r)
        label = f"w{r['i']}" if r["warmup"] else str(r["i"])
        status = str(r["status"]) if r["status"] is not None else r["error_kind"]
        note = " ".join(x for x in (r["note"], r["error_kind"] if r["status"] else "") if x)
        self.query_one("#calls", DataTable).add_row(label, status, fmt(r["seconds"]), note)
        measured = [x for x in self.results if not x["warmup"]]
        self.query_one("#spark", Sparkline).data = [x["seconds"] for x in measured if x["error_kind"] is None]
        self.query_one("#summary", Static).update("\n".join(summary_lines(summarize(measured, self.settings["n"]))))

    def finish(self):
        self.sub_title += "  (done, q to quit)"
