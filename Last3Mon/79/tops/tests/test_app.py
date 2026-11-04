"""R11 · R12: the TUI shows the areas, a tab that cannot read says so, and asking stays read only."""
from argparse import Namespace

from textual.widgets import DataTable, Input, Static

from conftest import DATA

from tops.app import OpsApp


async def test_areas_and_ask(fake):
    app = OpsApp(Namespace(n8n=fake.base, file=None, api=fake.base))
    async with app.run_test() as pilot:
        assert app.query_one("#area-table", DataTable).row_count == 6
        assert "overall 🔴 red" in str(app.query_one("#top", Static).render())
        await pilot.press("question_mark")
        app.query_one("#question", Input).value = "DLQ 1번 다시 돌려 줘"
        await pilot.press("enter")
        assert "refused (read_only)" in str(app.query_one("#answer", Static).render())
        assert app.query_one("#audit-table", DataTable).row_count == 3
    # tlog on the Tools tab reads the run logs too; nothing that changes state is ever called
    assert not {path for path, _ in fake.calls} & {"/dlq/update", "/dlq-clear", "/ops-reset", "/budget", "/admin/fault", "/release"}


async def test_file_mode_other_tabs_say_not_available(down):
    app = OpsApp(Namespace(n8n=None, file=str(DATA / "facts-cost-down.json"), api=down))
    async with app.run_test() as pilot:
        assert "sources down: cost" in str(app.query_one("#top", Static).render())
        assert app.query_one("#area-table", DataTable).row_count == 6
        await pilot.press("question_mark")
        app.query_one("#question", Input).value = "지난주 오류율이 얼마야?"
        await pilot.press("enter")
        assert "not available" in str(app.query_one("#answer", Static).render())
        assert "not available" in str(app.query_one("#audit-table", DataTable).get_row_at(0)[2])
