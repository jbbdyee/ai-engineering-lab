"""R11: summary on top, failure groups on the left ([t] switches to hours, slow runs), runs of the chosen group on the right."""
import argparse

from textual.widgets import DataTable, Static

from tlog.app import LogApp


def args(**kw):
    base = dict(file="tests/data/run-logs.json", url=None, date_from="2026-10-19", date_to="2026-10-30", tag="", source="all")
    return argparse.Namespace(**{**base, **kw})


async def test_screen():
    app = LogApp(args())
    async with app.run_test() as pilot:
        await pilot.pause()
        assert str(app.query_one("#top", Static).render()).startswith("666 runs · errors 21")
        groups = app.query_one("#groups", DataTable)
        assert groups.row_count == 2 and groups.get_row_at(0)[0] == 16          # FAQ timeout first
        assert app.query_one("#runs", DataTable).row_count == 16
        await pilot.press("down")
        await pilot.pause()
        assert app.query_one("#runs", DataTable).row_count == 5
        await pilot.press("t")                                                   # hours, most errors first
        await pilot.pause()
        assert groups.get_row_at(0)[0] == "2026-10-26T09"
        await pilot.press("t")                                                   # slow runs
        await pilot.pause()
        assert groups.row_count == 20
