"""Textual screen (R8): versions on the left, changed nodes as a tree on the right, the chosen change below.
`[s]` saves the file again as a new version, `[q]` quits."""
from pathlib import Path

from textual import work
from textual.app import App, ComposeResult
from textual.containers import Horizontal
from textual.widgets import Footer, Header, ListItem, ListView, Static, Tree

from . import diff
from .store import Store, safe_name
from .workflow import load


class VersionApp(App):
    TITLE = "tver"
    BINDINGS = [("s", "save", "Save file as a version"), ("q", "quit", "Quit")]
    CSS = """
    #summary { height: auto; margin: 0 1; }
    #versions { width: 40; border: round $accent; }
    #changes { border: round $accent; }
    #detail { height: 10; border: round $accent; padding: 0 1; }
    """

    def __init__(self, target, store: Store | None = None):
        super().__init__()
        self.file = Path(target) if Path(target).exists() else None
        self.name_ = safe_name(Path(target).name)
        self.store = store or Store()
        self.versions = []
        self.changes = []

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static("loading...", id="summary")
        with Horizontal():
            yield ListView(id="versions")
            yield Tree("changes", id="changes")
        yield Static("", id="detail")
        yield Footer()

    def on_mount(self):
        self.sub_title = f"{self.name_} · {self.store.repo}"
        self.reload()

    def reload(self):
        self.versions = self.store.log(self.name_)
        view = self.query_one(ListView)
        view.clear()
        for v in self.versions:
            view.append(ListItem(Static(f"{v.rev} {v.date[5:16]}  {v.message.split(': ', 1)[-1]}")))
        self.query_one("#summary", Static).update(
            f"{len(self.versions)} version(s)" + ("" if self.versions else f" · none yet: press [s] or run tver save {self.file or self.name_}"))
        if self.versions:
            view.index = 0
            self.compare(0)

    def on_list_view_highlighted(self, event):
        if event.list_view.index is not None and 0 <= event.list_view.index < len(self.versions):
            self.compare(event.list_view.index)

    @work(thread=True, exclusive=True)
    def compare(self, index: int):
        """The chosen version against the one before it (the oldest against nothing)."""
        new = self.store.show(self.versions[index].rev, self.name_)
        old = self.store.show(self.versions[index + 1].rev, self.name_) if index + 1 < len(self.versions) \
            else {"nodes": [], "connections": {}}
        self.call_from_thread(self.show_changes, index, diff.compare(old, new))

    def show_changes(self, index: int, changes):
        self.changes = changes
        tree = self.query_one(Tree)
        tree.clear()
        before = self.versions[index + 1].rev if index + 1 < len(self.versions) else "(empty)"
        tree.root.set_label(f"{before} → {self.versions[index].rev} · {diff.summary_line(diff.summary(changes))}")
        groups = {}
        for i, change in enumerate(changes):
            parent = groups.get(change.node)
            if parent is None:
                parent = groups[change.node] = tree.root.add(change.node, expand=True)
            parent.add_leaf(f"[{change.category}] {change.title()}", data=i)
        tree.root.expand()
        self.query_one("#detail", Static).update("choose a change" if changes else "no change")

    def on_tree_node_highlighted(self, event):
        index = event.node.data
        if index is None or not 0 <= index < len(self.changes):
            return
        change = self.changes[index]
        rows = [change.title()]
        rows += change.lines or [f"- {diff.short(change.before, 200)}", f"+ {diff.short(change.after, 200)}"] \
            if change.op == "~set" else []
        self.query_one("#detail", Static).update("\n".join(rows[:12]))

    def action_save(self):
        if not self.file:
            self.query_one("#summary", Static).update("open tver with a file path to save it")
            return
        status, message = self.store.save_workflow(load(self.file), self.name_)
        self.reload()
        self.query_one("#summary", Static).update(f"{status} {message}".strip() + f" · {len(self.versions)} version(s)")
