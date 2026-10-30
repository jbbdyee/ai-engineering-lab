"""R1 · R2 · R3 · R4 · R5 · R6 · R11 · R12 · R13 without a screen and without any API call."""
import datetime as dt
import json

import pytest

from tcost import tokens, usage, workflow
from tcost.prices import UnknownModel, load
from tcost.scan import scan

from conftest import DATA


def test_cost_formula(table):
    assert table.cost("gpt-4.1-mini", 1000) == 0.0004                    # 1,000 × 0.40 / 1M
    assert table.cost("gpt-4.1-mini", 1000, 100) == 0.00056              # R2: + 100 × 1.60 / 1M
    assert table.cost("gpt-5.4-nano", 100, 20) == 0.000045


def test_unknown_model_is_not_free(table):
    with pytest.raises(UnknownModel) as error:
        table.cost("gpt-9", 1000)
    assert "gpt-5.4-nano" in str(error.value)


def test_price_table_date(table, tmp_path):
    assert table.checked and table.source                                # R3: date and source with the prices
    assert table.warning(dt.date.fromisoformat(table.checked)) == ""
    assert "days ago" in table.warning(dt.date.fromisoformat(table.checked) + dt.timedelta(days=45))
    old = tmp_path / "old.json"
    old.write_text(json.dumps({"models": {"m": {"input": 1, "output": 2}}}), encoding="utf-8")
    assert "no 'checked' date" in load(old).warning()


def test_count_offline():
    assert tokens.count("") == 0
    assert 0 < tokens.count("VPN 접속이 자꾸 끊겨요") < tokens.count("VPN 접속이 자꾸 끊겨요. " * 10)


def test_workflow_steps():
    base = {s.node: s for s in workflow.llm_steps(workflow.load(DATA / "baseline-cost.json"))}
    lean = {s.node: s for s in workflow.llm_steps(workflow.load(DATA / "lab02-example1-lean.json"))}
    assert set(base) == {"Classify", "Answer", "Review"}
    assert base["Answer"].model == "gpt-4.1-mini"
    assert base["Answer"].system_tokens > 1000 > 200 > lean["Answer"].system_tokens   # the rules: R4
    assert lean["Answer"].max_out == 200 and base["Answer"].max_out is None


def test_not_a_workflow(tmp_path):
    path = tmp_path / "cases.json"
    path.write_text('{"webhook": "x", "cases": []}', encoding="utf-8")
    with pytest.raises(workflow.NotWorkflow):
        workflow.load(path)


def test_usage_from_reports(folder):
    found = usage.collect([folder / "runs"])
    assert (found.reports, found.requests, found.skipped) == (1, 2, 1)   # the 400 answer has no usage
    assert found.total["calls"] == 3 and found.total["cost_usd"] == 0.0007442
    assert found.by_user["이준호"]["cost_usd"] == 0.00056
    assert set(found.by_model) == {"gpt-4.1-mini", "gpt-5.4-nano"}
    assert found.by_hour == {"15h": found.total}
    assert found.month(1000, 22) == round(0.0007442 / 2 * 1000 * 22, 6)   # R6


def test_scan_sorts_folder(folder):
    found = scan(folder)
    assert [p.name for p in found.texts] == ["long.prompt", "short.txt"]
    assert len(found.workflows) == 2 and len(found.reports) == 1
    assert [p.name for p in found.skipped] == ["lab01.json"]             # R11: a test file is not a workflow
