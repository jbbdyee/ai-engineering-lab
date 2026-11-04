"""Textual screen (R11 · R12): status on top, five tabs (areas · brief · ask · audit · tools), [r] refresh, [?] ask, [q] quit.
The screen only shows what n8n already decided; a tab that cannot read says so and the others keep working."""
from __future__ import annotations

from textual.app import App, ComposeResult
from textual.widgets import DataTable, Footer, Header, Input, Markdown, Static, TabbedContent, TabPane

from . import client, view


class OpsApp(App):
    TITLE = "tops"
    BINDINGS = [("r", "refresh", "Refresh"), ("question_mark", "ask", "Ask"), ("q", "quit", "Quit")]
    CSS = "#top, #answer { height: auto; margin: 0 1; }"

    def __init__(self, args):
        super().__init__()
        self.args = args
        self.facts: dict | None = None

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static("", id="top", markup=False)
        with TabbedContent(id="tabs"):
            with TabPane("Areas", id="areas"):
                yield DataTable(id="area-table", cursor_type="row")
            with TabPane("Brief", id="brief"):
                yield Markdown("", id="brief-text")
            with TabPane("Ask", id="ask"):
                yield Input(placeholder="a question about operations, Enter to send (read only)", id="question")
                yield Static("", id="answer", markup=False)
            with TabPane("Audit", id="audit"):
                yield DataTable(id="audit-table", cursor_type="row")
            with TabPane("Tools", id="tools"):
                yield Static("", id="tool-text", markup=False)
        yield Footer()

    def on_mount(self):
        self.query_one("#area-table", DataTable).add_columns("", "area", "color", "numbers")
        self.query_one("#audit-table", DataTable).add_columns("area", "router", "result", "question")
        self.action_refresh()

    def read(self, what):
        try:
            return what(), ""
        except client.ReadError as error:
            return None, f"not available: {error}"

    def action_refresh(self):
        a = self.args
        self.facts, why = self.read(lambda: client.facts(a.n8n, a.file))
        top = self.query_one("#top", Static)
        table = self.query_one("#area-table", DataTable)
        table.clear()
        if self.facts is None:
            top.update(why)
        else:
            lines = view.status_lines(self.facts)
            top.update(lines[0] + (f"  ·  {lines[-1].strip()}" if self.facts.get("sources_down") else ""))
            for area in view.AREAS:
                color = self.facts["health"].get(area, "unknown")
                table.add_row(view.MARK.get(color, "?"), view.LABEL[area], color, view.numbers(self.facts, area), key=area)
        brief_text = self.query_one("#brief-text", Markdown)
        if not a.n8n:
            brief_text.update("not available: no --n8n (reading a file)")
        else:
            b, why = self.read(lambda: client.brief(a.n8n))
            brief_text.update(b.get("markdown", "") if b else why)
        audit = self.query_one("#audit-table", DataTable)
        audit.clear()
        events, why = self.read(lambda: client.audit(getattr(a, "api", None) or "http://localhost:8800").get("events", []))
        for e in events or []:
            audit.add_row(e.get("area", "-"), e.get("router", "-"), f"refused {e.get('reason')}" if e.get("refused") else "answered", e.get("question", ""))
        if events is None:
            audit.add_row("-", "-", why, "")
        api = getattr(a, "api", None) or "http://localhost:8800"
        parts = [view.tool("tlog", ["slo", "--url", api, "--from", "2026-10-26", "--to", "2026-10-30", "--json"]), view.tool("tcheck", ["--help"])]
        self.query_one("#tool-text", Static).update("\n".join(view.tool_line(part) for part in parts))

    def action_ask(self):
        self.query_one("#tabs", TabbedContent).active = "ask"
        self.query_one("#question", Input).focus()

    def on_input_submitted(self, event: Input.Submitted):
        question = event.value.strip()
        answer = self.query_one("#answer", Static)
        if not question:
            return
        if not self.args.n8n:
            answer.update("not available: no --n8n (reading a file)")
            return
        a, why = self.read(lambda: client.ask(self.args.n8n, question))
        answer.update("\n".join(view.answer_lines(a)) if a else why)
        self.query_one("#area-table", DataTable).focus()
