"""R1 · R7: the colors and numbers come from the facts unchanged."""
from conftest import load

from tops import view


def test_status_shows_every_area_with_the_facts_colors():
    lines = view.status_lines(load("facts.json"))
    assert lines[0].startswith("overall 🔴 red · runs 2026-10-26 ~ 2026-10-30")
    assert "  🔴 runs     error rate 5.88% · p95 2598ms · unanswered 4.76%" in lines
    assert "  🔴 DLQ      3 (parked 2)" in lines
    assert "  🟡 cost     $0.073604 / $0.08 (92.01%)" in lines
    assert "  🔴 release  1.1.0 · canary 1.2.0 20% (repeat 62.5%)" in lines


def test_source_down_is_unknown_not_zero():
    lines = view.status_lines(load("facts-cost-down.json"))
    assert "  ⚪ cost     source not answering" in lines
    assert lines[-1] == "  sources down: cost"


def test_colors_are_not_recounted():
    f = load("facts.json")
    f["health"]["cost"] = "green"          # n8n says green: tops shows green even at 92%
    assert any(line.startswith("  🟢 cost") for line in view.status_lines(f))


def test_answer_lines_refused_and_checked():
    asks = load("asks.json")
    assert view.answer_lines(asks["DLQ 1번 다시 돌려 줘"])[0] == "[action · keyword] refused (read_only)"
    assert view.answer_lines(asks["지난주 오류율이 얼마야?"])[0] == "[runs · keyword] numbers ✔"


def test_missing_tool_is_reported_not_raised():
    part = view.tool("no-such-course-tool", ["--json"])
    assert part == {"tool": "no-such-course-tool", "ok": False, "why": "not installed (uv tool install)"}


def test_tool_line_reads_tlog_slo():
    part = {"tool": "tlog", "ok": True, "code": 4, "result": {"ok": False, "breaches": ["error_rate", "unanswered_rate"], "total": 357}}
    assert view.tool_line(part) == "  ✔ tlog slo: breaches error_rate, unanswered_rate (357 runs)"
