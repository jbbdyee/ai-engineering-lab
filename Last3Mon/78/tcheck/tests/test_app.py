import json
from types import SimpleNamespace

from tcheck import checks, load
from tcheck.app import CheckApp
from conftest import DATA


def make(tmp_path):
    rows, _ = load.read_rows(str(DATA / "employees.csv"))
    schema = json.loads((DATA / "schemas" / "employee.json").read_text())
    args = SimpleNamespace(file=str(DATA / "employees.csv"), out=str(tmp_path / "clean.csv"))
    return CheckApp(args, rows, schema, checks.check(rows, schema, "HR-1"))


async def test_tabs_filter_and_export(tmp_path):
    app = make(tmp_path)
    async with app.run_test() as pilot:
        assert "9 rows · valid 4" in str(app.query_one("#top").render())
        assert app.query_one("#problem-table").row_count == 5
        assert app.query_one("#code-table").row_count == 5
        assert app.query_one("#clean-table").row_count == 4
        await pilot.press("slash")
        await pilot.pause()
        for key in "email":
            await pilot.press(key)
        await pilot.press("enter")
        assert app.query_one("#problem-table").row_count == 1
        await pilot.press("escape")
        assert app.query_one("#problem-table").row_count == 5
        await pilot.press("e")
        assert app.exported.endswith("clean.csv") and (tmp_path / "clean.csv").read_text().count("\n") == 5
