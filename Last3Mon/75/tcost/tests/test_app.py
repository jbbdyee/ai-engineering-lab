"""R8: the three tabs fill from one folder, without calling any API."""
from textual.widgets import DataTable, TabbedContent

from tcost.app import CostApp


async def test_tabs(folder, table):
    app = CostApp(str(folder), table)
    async with app.run_test() as pilot:
        await pilot.pause()
        prompts = app.query_one("#prompt-table", DataTable)
        assert prompts.row_count == 2 + 6                     # two prompt files + six LLM steps of two workflows
        app.query_one(TabbedContent).active = "usage"
        await pilot.pause()
        assert "2 request(s)" in str(app.query_one("#usage-head").render())
        assert "15h" in str(app.query_one("#hours").render())
        assert app.query_one("#compare-table", DataTable).row_count == 8
