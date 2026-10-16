import json
from pathlib import Path

import pytest

from miniflow import load_workflow, run_workflow
from miniflow.tools import parse_actions

ROOT = Path(__file__).resolve().parents[1]
NOTES = json.loads((ROOT / "data" / "meeting-notes.json").read_text(encoding="utf-8"))


@pytest.fixture(autouse=True)
def isolated(tmp_path, monkeypatch):
    monkeypatch.setenv("MINIFLOW_MEMORY_FILE", str(tmp_path / "memory.json"))
    monkeypatch.setenv("MINIFLOW_LLM", "mock")


def run(inputs):
    return run_workflow(load_workflow(ROOT / "flows" / "08-meeting-actions.json"), inputs, verbose=False)


def test_weekly_meeting_gives_four_actions_with_defaults():
    report = run(NOTES["weekly"])
    assert report["result"]["route"] == "할 일 정리"
    assert report["result"]["count"] == 4
    assert report["result"]["actions"][3] == {"task": "회의실 예약 규칙 개선 담당자 지정", "owner": "미정", "due": "미정"}


def test_meeting_without_actions():
    report = run(NOTES["no_action"])
    assert report["result"]["route"] == "할 일 없음"
    statuses = {step["id"]: step["status"] for step in report["trace"]}
    assert statuses["report"] == "skipped"


def test_empty_notes_rejected_before_llm():
    report = run({"title": "빈 회의록", "notes": ""})
    assert report["result"] == {"error": "notes is required"}
    statuses = {step["id"]: step["status"] for step in report["trace"]}
    assert statuses["extract"] == statuses["summarize"] == "skipped"


@pytest.mark.parametrize("text,count", [
    ('{"actions": [{"task": "보고서 작성", "owner": "김", "due": "금"}]}', 1),
    ('```json\n{"actions": [{"task": "A", "owner": "", "due": null}]}\n```', 1),
    ('[{"task": "목록 형태", "owner": "이"}]', 1),
    ('{"actions": [{"task": ""}, "문자열"]}', 0),
    ("할 일이 없습니다", 0),
])
def test_parse_actions(text, count):
    assert parse_actions(text)["count"] == count
