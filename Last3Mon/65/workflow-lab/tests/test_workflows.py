import json
from pathlib import Path

import pytest

from miniflow import WorkflowError, load_workflow, run_workflow
from miniflow.template import TemplateError, render

FLOWS = Path(__file__).resolve().parents[1] / "flows"


@pytest.fixture(autouse=True)
def isolated_memory(tmp_path, monkeypatch):
    monkeypatch.setenv("MINIFLOW_MEMORY_FILE", str(tmp_path / "memory.json"))
    monkeypatch.setenv("MINIFLOW_LLM", "mock")


def run(name, **inputs):
    return run_workflow(load_workflow(FLOWS / name), inputs, verbose=False)


def test_every_sample_flow_is_valid():
    for path in FLOWS.glob("*.json"):
        assert load_workflow(path).order()


def test_template_keeps_type_for_whole_placeholder():
    context = {"nodes": {"tool": {"output": {"temp": 20}}}}
    assert render("{{nodes.tool.output}}", context) == {"temp": 20}
    assert render("temp={{nodes.tool.output.temp}}", context) == "temp=20"
    with pytest.raises(TemplateError):
        render("{{nodes.missing.output}}", context)


def test_llm_only():
    report = run("01-llm-only.json", text="오늘 회의에서 일정이 확정되었습니다.")
    assert report["status"] == "completed"
    assert "Mock" in report["result"]


def test_tool_data_flows_into_llm():
    report = run("02-llm-tool.json", city="제주", question="우산이 필요할까?")
    assert "제주" in report["result"] and "80%" in report["result"]


def test_unknown_city_fails_at_tool_node():
    report = run("02-llm-tool.json", city="평양", question="날씨?")
    assert report["status"] == "failed"
    assert report["trace"][-1]["id"] == "weather"


def test_memory_survives_between_runs():
    run("03-save-profile.json", user="minji", preference="실내 전시")
    report = run("04-recommend-with-memory.json", user="minji", city="부산")
    assert "실내 전시" in report["result"]
    again = run("04-recommend-with-memory.json", user="minji", city="강릉")
    recall = next(step for step in again["trace"] if step["id"] == "recall")
    assert recall["output"]["last_city"] == "부산"


def test_tech_support_ticket():
    report = run("05-tech-support-ticket.json", user="kim", ticket="비밀번호를 잊어버려서 로그인이 안 돼요")
    assert report["result"]["category"] == "account"
    assert report["result"]["faq_id"] == "FAQ-001"


def test_cycle_is_rejected(tmp_path):
    flow = {
        "nodes": [{"id": "a", "type": "input"}, {"id": "b", "type": "output", "value": "x"}],
        "edges": [["a", "b"], ["b", "a"]],
    }
    path = tmp_path / "cycle.json"
    path.write_text(json.dumps(flow), encoding="utf-8")
    with pytest.raises(WorkflowError):
        load_workflow(path)


def test_missing_input_is_reported():
    with pytest.raises(WorkflowError):
        run("02-llm-tool.json", city="서울")
