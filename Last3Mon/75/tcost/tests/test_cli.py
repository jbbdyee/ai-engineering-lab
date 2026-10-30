"""R7 · R9 · R10 · R12: commands, --json and exit codes (0 fine · 1 over --max-usd · 2 error)."""
import json

import pytest

from tcost.cli import main


def run(capsys, *argv):
    with pytest.raises(SystemExit) as end:
        main(list(argv))
    out = capsys.readouterr()
    return end.value.code, out.out, out.err


def test_count_and_gate(capsys, folder):
    code, out, _ = run(capsys, "count", str(folder / "prompts"), "--out", "100")
    assert code == 0 and "long.prompt" in out and "gpt-5.4-nano /call" in out
    code, _, err = run(capsys, "count", str(folder / "prompts" / "long.prompt"), "--out", "200", "--max-usd", "0.0002")
    assert code == 1 and "more than --max-usd" in err
    code, out, _ = run(capsys, "count", str(folder / "prompts" / "short.txt"), "--json", "--model", "gpt-4.1-mini")
    assert code == 0 and json.loads(out)["rows"][0]["tokens"] > 0


def test_unknown_model_and_missing_file(capsys, folder):
    code, _, err = run(capsys, "count", str(folder / "prompts"), "--model", "gpt-9")
    assert code == 2 and "unknown model 'gpt-9'" in err
    code, _, err = run(capsys, "count", str(folder / "nothing.txt"))
    assert code == 2 and "no such file" in err


def test_compare_and_budget(capsys, folder):
    code, out, _ = run(capsys, "compare", str(folder / "prompts" / "long.prompt"), "--model", "gpt-4.1-mini",
                       "--model", "gpt-5.4-nano", "--out", "100")
    assert code == 0 and "cheaper than gpt-4.1-mini" in out
    code, out, _ = run(capsys, "budget", "1.0", str(folder / "prompts" / "short.txt"), "--out", "100", "--json")
    rows = json.loads(out)
    assert code == 0 and rows["gpt-5.4-nano"]["calls"] > rows["gpt-4.1-mini"]["calls"]


def test_usage_and_workflow(capsys, folder):
    code, out, _ = run(capsys, "usage", str(folder / "runs"), "--per-day", "1000")
    assert code == 0 and "2 request(s)" in out and "skipped 1" in out and "month:" in out
    code, out, _ = run(capsys, "workflow", str(folder / "reference"), "--json")
    steps = json.loads(out)["steps"]
    assert code == 0 and len(steps) == 6
