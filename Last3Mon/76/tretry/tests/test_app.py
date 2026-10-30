"""R11: the screen ranks targets by failed tries and lists the tries of the chosen one."""
from textual.widgets import DataTable

from tretry import log
from tretry.app import LogApp
from tretry.retry import Attempt, Result


def make_log(tmp_path):
    path = tmp_path / "log.jsonl"
    log.write(path, "http", "POST http://x/tickets", Result(False, attempts=[Attempt(1, 0, 3, False, "timeout"), Attempt(2, 3.5, 3, False, "timeout")],
                                                           stopped="tries", seconds=6.5), now=100)
    log.write(path, "command", "curl ok", Result(True, attempts=[Attempt(1, 0, 0.1, True)], stopped="success", seconds=0.1), now=101)
    return path


async def test_tables(tmp_path):
    app = LogApp(make_log(tmp_path))
    async with app.run_test() as pilot:
        await pilot.pause()
        targets = app.query_one("#targets", DataTable)
        assert targets.row_count == 2 and targets.get_row_at(0)[0] == "POST http://x/tickets"   # most failures first
        assert app.query_one("#tries", DataTable).row_count == 2
        await pilot.press("down")
        await pilot.pause()
        assert app.query_one("#tries", DataTable).row_count == 1
        await pilot.press("f")
        await pilot.pause()
        assert app.query_one("#tries", DataTable).row_count == 0
