"""Textual screen: findings table, masked preview of the lines around the chosen one, [i] to ignore."""
from pathlib import Path

from textual import work
from textual.app import App, ComposeResult
from textual.widgets import DataTable, Footer, Header, Static

from .files import add_ignore, env_values_from, is_env_file, iter_files, load_rules, read_text, scan_folder
from .scanner import mask_line


class ScanApp(App):
    TITLE = "tscan"
    BINDINGS = [("i", "ignore", "Ignore (add to .tscanignore)"), ("r", "rescan", "Rescan"), ("q", "quit", "Quit")]
    CSS = """
    #summary { height: auto; margin: 0 1; }
    DataTable { height: 1fr; }
    #preview { height: 7; border: round $accent; padding: 0 1; }
    """

    def __init__(self, root):
        super().__init__()
        self.root = Path(root)
        self.found = []
        self.env_values = []

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static("scanning...", id="summary")
        yield DataTable(id="found", cursor_type="row")
        yield Static("", id="preview")
        yield Footer()

    def on_mount(self):
        self.query_one(DataTable).add_columns("kind", "file", "line", "value")
        self.sub_title = str(self.root)
        self.scan()

    @work(thread=True, exclusive=True)
    def scan(self):
        found, report = scan_folder(self.root)
        values = set()
        for path in iter_files(self.root):
            if is_env_file(path.name):
                text, _ = read_text(path)
                values |= env_values_from(text or "")
        self.call_from_thread(self.show, found, report, sorted(values, key=len, reverse=True))

    def show(self, found, report, env_values):
        self.found, self.env_values = found, env_values
        table = self.query_one(DataTable)
        table.clear()
        for f in found:
            table.add_row(f.kind, f.path, str(f.line), f.masked)
        skipped = sum(report["skipped"].values())
        self.query_one("#summary", Static).update(f"files {report['files']} · found {len(found)} · skipped {skipped}")
        self.query_one("#preview", Static).update("" if found else "nothing found")

    def preview_lines(self, finding, around=2):
        text, _ = read_text(self.root / finding.path)
        lines = (text or "").splitlines()
        rules = load_rules(self.root)
        start = max(1, finding.line - around)
        rows = []
        for n in range(start, min(len(lines), finding.line + around) + 1):
            mark = ">" if n == finding.line else " "
            rows.append(f"{mark}{n:4}  {mask_line(lines[n - 1], rules, self.env_values)}")
        return "\n".join(rows)

    def on_data_table_row_highlighted(self, event):
        if 0 <= event.cursor_row < len(self.found):
            self.query_one("#preview", Static).update(self.preview_lines(self.found[event.cursor_row]))

    def action_ignore(self):
        row = self.query_one(DataTable).cursor_row
        if 0 <= row < len(self.found):
            f = self.found[row]
            add_ignore(self.root, f"{f.path}:{f.line}")
            self.scan()

    def action_rescan(self):
        self.scan()
