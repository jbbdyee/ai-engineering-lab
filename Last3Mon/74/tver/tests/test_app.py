"""R8: versions list, change tree, detail of the chosen change, [s] saves."""
import asyncio
import json

from textual.widgets import ListView, Tree

from tver.app import VersionApp
from tver.store import Store


async def wait_for(pilot, check):
    for _ in range(60):
        await asyncio.sleep(0.05)
        await pilot.pause()
        if check():
            return True
    return False


async def test_versions_tree_and_save(work, store_dir, v2):
    store = Store(store_dir)
    store.save(work / "helpdesk.json")
    (work / "helpdesk.json").write_text(json.dumps(v2), encoding="utf-8")
    app = VersionApp(str(work / "helpdesk.json"), store)
    async with app.run_test() as pilot:
        assert len(app.query_one(ListView).children) == 1
        await pilot.press("s")
        assert await wait_for(pilot, lambda: len(app.query_one(ListView).children) == 2)
        assert await wait_for(pilot, lambda: "model 1 · prompt 1 · flow 5" in str(app.query_one(Tree).root.label))
        tree = app.query_one(Tree)
        tree.focus()
        await pilot.press("down", "down")
        await pilot.pause()
        assert str(app.query_one("#detail").render()).strip() != ""
