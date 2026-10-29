"""R1 · R2 · R3 · R4 · R11 · R12 with the day 74 v1 → v2 files."""
import copy
import json

from tver import diff
from tver.cli import main
from tver.workflow import clean, dumps


def test_v1_to_v2_is_seven_changes_like_flow_py(v1, v2):
    changes = diff.compare(v1, v2)
    titles = [c.title() for c in changes]
    assert "+ node 'Review check' (code)" in titles
    assert any(t.startswith("~ 'Answer' parameters.options.systemMessage: changed") for t in titles)
    assert "~ 'Answer model' parameters.model.value: gpt-4.1-mini → gpt-5.4-nano" in titles
    assert "~ 'Question webhook' parameters.path: rel-v1 → rel-v2" in titles
    s = diff.summary(changes)
    assert (s["total"], s["model"], s["prompt"], s["flow"]) == (7, 1, 1, 5)
    assert s["links"] == {"+": 2, "-": 1}


def test_noise_is_not_a_change(v1):
    moved = copy.deepcopy(v1)
    for node in moved["nodes"]:
        node["position"] = [node["position"][0] + 100, 0]
        node["id"] = "other-" + node["name"]
    moved["nodes"].reverse()
    assert diff.compare(v1, moved) == []
    assert dumps(v1) == dumps(moved)
    assert all("position" not in n and "id" not in n for n in clean(v1)["nodes"])


def test_long_prompt_gets_line_diff(v1, v2):
    change = next(c for c in diff.compare(v1, v2) if c.key.endswith("systemMessage"))
    assert change.category == "prompt"
    assert any(row.startswith("+") and "[FAQ-003]" in row for row in change.lines)


def test_renamed_node_is_paired(v1):
    renamed = copy.deepcopy(v1)
    for node in renamed["nodes"]:
        if node["name"] == "Search FAQ":
            node["name"] = "Find FAQ"
    conn = json.dumps(renamed["connections"]).replace('"Search FAQ"', '"Find FAQ"')
    renamed["connections"] = json.loads(conn)
    changes = diff.compare(v1, renamed)
    assert [c.op for c in changes] == ["renamed"]
    assert (changes[0].before, changes[0].after) == ("Search FAQ", "Find FAQ")


def test_cli_diff_exit_codes_and_json(tmp_path, v1, v2, capsys):
    a, b = tmp_path / "a.json", tmp_path / "b.json"
    a.write_text(json.dumps(v1), encoding="utf-8")
    b.write_text(json.dumps(v2), encoding="utf-8")
    assert main(["diff", str(a), str(a)]) == 0
    capsys.readouterr()
    assert main(["diff", str(a), str(b), "--json"]) == 1
    out = json.loads(capsys.readouterr().out)
    assert out["summary"]["total"] == 7
    assert main(["diff", str(a), str(tmp_path / "missing.json")]) == 2
