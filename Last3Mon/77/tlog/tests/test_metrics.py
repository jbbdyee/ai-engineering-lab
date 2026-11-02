"""R2 · R3 · R4 · R6 · R7: the definitions of AGENTS.md 3, and the same numbers as my-log-report on the two weeks."""
from tlog import load, metrics


def period(rows, a, b):
    return [r for r in rows if load.keep(r, a, b)]


def test_percentile_is_nearest_rank():
    values = list(range(1, 11))          # 1..10
    assert metrics.pct(values, 0.95) == 10 and metrics.pct(values, 0.5) == 5
    assert metrics.pct([], 0.95) == 0


def test_rate_rounds_like_javascript_and_zero_is_zero():
    assert metrics.rate(21, 666) == 0.0315 and metrics.rate(0, 0) == 0
    assert metrics.js_round(0.00005, 4) == 0.0001   # half up, like Math.round


def test_two_weeks_same_numbers_as_my_log_report(two_weeks):
    r = metrics.report(period(two_weeks, "2026-10-19", "2026-10-30"))
    assert (r["total"], r["errors"], r["error_rate"], r["p50_ms"], r["p95_ms"]) == (666, 21, 0.0315, 1205, 2537)
    assert r["by_route"] == {"자동 답변": 591, "담당자 연결": 34, "잠시 후": 20, "오류": 21}
    assert r["by_day"]["2026-10-26"] == {"total": 70, "errors": 16, "error_rate": 0.2286} and "2026-10-24" not in r["by_day"]
    assert r["by_release"]["1.2.0"] == {"answers": 8, "repeats": 5, "repeat_rate": 0.625}


def test_weeks_and_one_day(two_weeks):
    w2 = metrics.report(period(two_weeks, "2026-10-26", "2026-10-30"))
    assert (w2["total"], w2["errors"], w2["error_rate"], w2["p95_ms"]) == (357, 21, 0.0588, 2598)
    monday = metrics.report(period(two_weeks, "2026-10-26", "2026-10-26"))
    assert (monday["total"], monday["errors"]) == (70, 16)
    assert monday["steps"]["faq_ms"]["p95"] == 1000


def test_problems_and_anomalies(two_weeks):
    r = metrics.report(period(two_weeks, "2026-10-19", "2026-10-30"))
    assert r["failures"][0] == {"node": "Search FAQ", "message": "timeout of 1000ms exceeded", "count": 16}
    assert r["failures"][1]["node"] == "Answer" and r["failures"][1]["count"] == 5
    assert r["unanswered_topics"] == [{"topic": "와이파이", "count": 34}]
    assert [a["hour"] for a in r["anomalies"]] == ["2026-10-26T09", "2026-10-29T15"]
    assert r["repeat_topics"][0] == {"topic": "프린터", "answers": 81, "repeats": 8, "repeat_rate": 0.0988}
    assert metrics.report(period(two_weeks, "2026-10-19", "2026-10-23"))["anomalies"] == []


def test_steps_and_cost(two_weeks):
    r = metrics.report(period(two_weeks, "2026-10-19", "2026-10-30"))
    assert r["steps"]["faq_ms"] == {"runs": 646, "p50": 27, "p95": 39}
    assert r["steps"]["answer_ms"] == {"runs": 596, "p50": 1179, "p95": 2509}
    assert (r["cost_usd"], r["cost_per_run"], r["llm_calls"]) == (0.07836, 0.000118, 596)


def test_slo(two_weeks):
    w2 = metrics.report(period(two_weeks, "2026-10-26", "2026-10-30"))
    assert w2["unanswered_rate"] == 0.0476 and w2["slo"]["breaches"] == ["error_rate", "unanswered_rate"]
    w1 = metrics.report(period(two_weeks, "2026-10-19", "2026-10-23"), {"unanswered_rate": 0.06})
    assert w1["slo"]["ok"] is True


def test_empty_period_is_zero_not_null():
    r = metrics.report([])
    assert (r["total"], r["error_rate"], r["p95_ms"], r["cost_per_run"], r["anomalies"]) == (0, 0, 0, 0, [])


def test_weekly_markdown(two_weeks):
    now = metrics.report(period(two_weeks, "2026-10-26", "2026-10-30"))
    prev = metrics.report(period(two_weeks, "2026-10-19", "2026-10-23"))
    text = metrics.weekly_markdown(now, prev, "2026-10-26", "2026-10-30")
    assert "| 요청 | 309 | 357 |" in text and "| 오류율 | 0% | 5.88% |" in text
    assert "2026-10-26 09시 · 16/16" in text and "FAQ에 '와이파이' 항목 추가" in text
