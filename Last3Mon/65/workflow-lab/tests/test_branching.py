import json
from pathlib import Path

import pytest

from miniflow import WorkflowError, load_workflow, run_workflow
from miniflow.engine import evaluate_check

FLOWS = Path(__file__).resolve().parents[1] / "flows"


@pytest.fixture(autouse=True)
def isolated(tmp_path, monkeypatch):
    monkeypatch.setenv("MINIFLOW_MEMORY_FILE", str(tmp_path / "memory.json"))
    monkeypatch.setenv("MINIFLOW_LLM", "mock")


def statuses(report):
    return {step["id"]: step["status"] for step in report["trace"]}


def test_condition_true_branch_gives_auto_reply():
    report = run_workflow(load_workflow(FLOWS / "06-request-with-condition.json"),
                          {"user": "kim", "text": "VPN 접속이 계속 끊겨요"}, verbose=False)
    assert report["status"] == "completed"
    assert report["result"]["route"] == "자동 답변"
    assert report["result"]["faq_id"] == "FAQ-003"
    assert statuses(report)["hand_off"] == "skipped"


def test_condition_false_branch_hands_off():
    report = run_workflow(load_workflow(FLOWS / "06-request-with-condition.json"),
                          {"user": "lee", "text": "점심 메뉴 추천해줘"}, verbose=False)
    assert report["status"] == "completed"
    assert report["result"]["route"] == "담당자 확인"
    assert statuses(report)["draft"] == "skipped"


@pytest.mark.parametrize("text,team", [
    ("비밀번호를 잊어버렸어요", "계정 관리 담당"),
    ("프린터 출력이 안 돼요", "장비 지원 담당"),
    ("회의실 예약은 어떻게 하나요", "IT 문의 접수 창구"),
])
def test_switch_routes(text, team):
    report = run_workflow(load_workflow(FLOWS / "07-route-by-category.json"), {"text": text}, verbose=False)
    assert report["result"]["team"] == team


def test_join_after_exclusive_branches_runs(tmp_path):
    flow = {
        "inputs": ["n"],
        "nodes": [
            {"id": "start", "type": "input"},
            {"id": "big", "type": "condition", "check": {"left": "{{input.n}}", "op": "gt", "right": 10}},
            {"id": "yes", "type": "output", "value": "big"},
            {"id": "no", "type": "output", "value": "small"},
            {"id": "done", "type": "output", "value": "done"},
        ],
        "edges": [["start", "big"], ["big", "yes", "true"], ["big", "no", "false"], ["yes", "done"], ["no", "done"]],
    }
    path = tmp_path / "join.json"
    path.write_text(json.dumps(flow), encoding="utf-8")
    report = run_workflow(load_workflow(path), {"n": "3"}, verbose=False)
    assert statuses(report) == {"start": "ok", "big": "ok", "yes": "skipped", "no": "ok", "done": "ok"}


def test_branch_label_validation(tmp_path):
    flow = {
        "nodes": [{"id": "a", "type": "input"}, {"id": "b", "type": "output", "value": 1}],
        "edges": [["a", "b", "true"]],
    }
    path = tmp_path / "bad.json"
    path.write_text(json.dumps(flow), encoding="utf-8")
    with pytest.raises(WorkflowError):
        load_workflow(path)


@pytest.mark.parametrize("check,expected", [
    ({"left": "abc", "op": "contains", "right": "b"}, True),
    ({"left": "", "op": "empty"}, True),
    ({"left": "network", "op": "in", "right": ["network", "device"]}, True),
    ({"left": "5", "op": "lt", "right": 3}, False),
])
def test_evaluate_check(check, expected):
    assert evaluate_check(check, {"input": {}, "nodes": {}}) is expected


def test_branch_gate_blocks_even_with_other_plain_input(tmp_path):
    """A node behind a skipped condition stays skipped even if another plain edge reaches it."""
    flow = json.loads((FLOWS / "06-request-with-condition.json").read_text(encoding="utf-8"))
    flow["nodes"].insert(1, {"id": "is_urgent", "type": "condition",
                             "check": {"left": "{{input.text}}", "op": "contains", "right": "긴급"}})
    flow["nodes"].append({"id": "urgent_call", "type": "output", "value": {"route": "긴급 담당자 연결"}})
    flow["edges"] += [["start", "is_urgent"], ["is_urgent", "urgent_call", "true"], ["is_urgent", "has_faq", "false"]]
    path = tmp_path / "urgent.json"
    path.write_text(json.dumps(flow, ensure_ascii=False), encoding="utf-8")

    urgent = run_workflow(load_workflow(path), {"user": "kim", "text": "긴급! VPN이 끊겼어요"}, verbose=False)
    assert urgent["result"]["route"] == "긴급 담당자 연결"
    assert statuses(urgent)["draft"] == "skipped"

    normal = run_workflow(load_workflow(path), {"user": "kim", "text": "VPN이 끊겼어요"}, verbose=False)
    assert normal["result"]["route"] == "자동 답변"
    assert statuses(normal)["urgent_call"] == "skipped"
