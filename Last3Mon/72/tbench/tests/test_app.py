"""R2 · R5: rows appear while calls are still running; picking a body file starts the run."""
import asyncio

from textual.widgets import DataTable, OptionList

from tbench.app import BenchApp
from tbench.cli import settings_from


def settings(url, n, body_file=None):
    return settings_from(type("A", (), {"url": url, "n": n, "body_file": body_file})())


async def test_rows_arrive_one_by_one(server, body_file):
    app = BenchApp(settings(server.base + "?delay=0.5", 6, str(body_file)), {})
    async with app.run_test() as pilot:
        await asyncio.sleep(1.3)
        partial = app.query_one("#calls", DataTable).row_count
        assert 1 <= partial < 6
        await asyncio.sleep(2.5)
        await pilot.pause()
        assert app.query_one("#calls", DataTable).row_count == 6
        assert "done 6/6" in str(app.query_one("#summary").render())


async def test_pick_a_body(server, body_file):
    app = BenchApp(settings(server.base, 2), {}, pick=str(body_file.parent))
    async with app.run_test() as pilot:
        assert app.query_one(OptionList).option_count == 1
        await pilot.press("enter")
        await asyncio.sleep(0.5)
        await pilot.pause()
        assert app.query_one("#calls", DataTable).row_count == 2
        assert server.bodies
