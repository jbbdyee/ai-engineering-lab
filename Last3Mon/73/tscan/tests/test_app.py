"""R8: table, masked preview, [i] ignore."""
import asyncio

from conftest import FAKE_EMAIL, FAKE_KEY, FAKE_PHONE
from textual.widgets import DataTable

from tscan.app import ScanApp


async def wait_rows(app, pilot, n=None):
    for _ in range(50):
        await asyncio.sleep(0.05)
        await pilot.pause()
        rows = app.query_one(DataTable).row_count
        if rows and (n is None or rows == n):
            return rows
    return app.query_one(DataTable).row_count


async def test_table_preview_and_ignore(fake):
    app = ScanApp(fake)
    async with app.run_test() as pilot:
        assert await wait_rows(app, pilot) == 5
        await pilot.press("down")
        await pilot.pause()
        preview = str(app.query_one("#preview").render())
        for secret in (FAKE_KEY, FAKE_PHONE, FAKE_EMAIL):
            assert secret not in preview
        assert "010-****-1234" in preview
        await pilot.press("i")
        assert await wait_rows(app, pilot, 4) == 4
    assert (fake / ".tscanignore").read_text() == "notes.md:1\n"
