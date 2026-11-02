"""The metrics of AGENTS.md 3 (R2 · R3 · R4 · R6 · R7), the comparison (R8) and the weekly report (R10).
Same names and the same numbers as the n8n workflow my-log-report."""
from __future__ import annotations

import math
from collections import defaultdict

DEFAULT_SLO = {"error_rate": 0.01, "p95_ms": 3000, "unanswered_rate": 0.02}


def pct(values: list[float], p: float) -> float:
    """Nearest rank: sorted ascending, the ceil(p × n)-th value (1-based). 0 when empty."""
    if not values:
        return 0
    ordered = sorted(values)
    return ordered[max(0, math.ceil(p * len(ordered)) - 1)]


def js_round(value: float, digits: int) -> float:
    """Like JavaScript Math.round(value × 10^d) / 10^d (half up), so the numbers match the n8n Code node exactly."""
    scale = 10 ** digits
    out = math.floor(value * scale + 0.5) / scale
    return int(out) if out == int(out) else out


def rate(part: float, whole: float) -> float:
    """Rounded to 4 decimals, 0 when the whole is 0."""
    return js_round(part / whole, 4) if whole else 0


def summary(rows: list[dict]) -> dict:
    """R2: total · errors · error_rate · p50_ms · p95_ms · by_route (null -> 오류) · by_day · by_release."""
    errors = sum(1 for r in rows if r.get("status") == "error")
    by_route: dict[str, int] = {}
    for r in rows:
        key = r.get("route") or "오류"
        by_route[key] = by_route.get(key, 0) + 1
    durations = [r.get("duration_ms", 0) for r in rows]
    days: dict[str, list] = defaultdict(list)
    for r in rows:
        days[str(r.get("started_at", ""))[:10]].append(r)
    by_day = {}
    for day in sorted(days):
        e = sum(1 for r in days[day] if r.get("status") == "error")
        by_day[day] = {"total": len(days[day]), "errors": e, "error_rate": rate(e, len(days[day]))}
    by_release: dict[str, dict] = {}
    for r in rows:
        if r.get("route") == "자동 답변":
            b = by_release.setdefault(str(r.get("release")), {"answers": 0, "repeats": 0})
            b["answers"] += 1
            b["repeats"] += bool(r.get("repeat"))
    for b in by_release.values():
        b["repeat_rate"] = rate(b["repeats"], b["answers"])
    return {"total": len(rows), "errors": errors, "error_rate": rate(errors, len(rows)), "p50_ms": pct(durations, 0.5),
            "p95_ms": pct(durations, 0.95), "by_route": by_route, "by_day": by_day, "by_release": by_release}


def steps_and_cost(rows: list[dict]) -> dict:
    """R6: per step only the runs that went through it (value > 0); cost sum (5 decimals), per run (6), LLM calls."""
    steps = {}
    for key in ("faq_ms", "answer_ms"):
        values = [v for v in ((r.get("steps") or {}).get(key, 0) for r in rows) if v and v > 0]
        steps[key] = {"runs": len(values), "p50": pct(values, 0.5), "p95": pct(values, 0.95)}
    cost = js_round(sum(r.get("cost_usd") or 0 for r in rows), 5)
    return {"steps": steps, "cost_usd": cost, "cost_per_run": js_round(cost / len(rows), 6) if rows else 0,
            "llm_calls": sum(r.get("llm_calls") or 0 for r in rows)}


def problems(rows: list[dict]) -> dict:
    """R3: failures by (node, message), unanswered topics, topics answered but asked again."""
    fails: dict[tuple, int] = defaultdict(int)
    for r in rows:
        if r.get("status") == "error":
            fails[(r.get("error_node"), r.get("error_message"))] += 1
    failures = sorted(({"node": n, "message": m, "count": c} for (n, m), c in fails.items()), key=lambda f: -f["count"])
    unanswered: dict[str, int] = defaultdict(int)
    for r in rows:
        if r.get("route") == "담당자 연결":
            unanswered[r.get("topic")] += 1
    topics = sorted(({"topic": t, "count": c} for t, c in unanswered.items()), key=lambda u: -u["count"])
    rep: dict[str, dict] = {}
    for r in rows:
        if r.get("route") == "자동 답변":
            t = rep.setdefault(r.get("topic"), {"topic": r.get("topic"), "answers": 0, "repeats": 0})
            t["answers"] += 1
            t["repeats"] += bool(r.get("repeat"))
    repeat_topics = sorted(({**t, "repeat_rate": rate(t["repeats"], t["answers"])} for t in rep.values() if t["repeats"] > 0),
                           key=lambda t: (-t["repeat_rate"], -t["repeats"]))
    return {"failures": failures, "unanswered_topics": topics, "repeat_topics": repeat_topics}


def anomalies(rows: list[dict], error_rate: float) -> list[dict]:
    """R4: hours (started_at[:13]) with at least 5 runs, an error rate >= 3 × the period's, and at least 1 error."""
    hours: dict[str, list] = defaultdict(list)
    for r in rows:
        hours[str(r.get("started_at", ""))[:13]].append(r)
    out = []
    for hour in sorted(hours):
        group = hours[hour]
        e = sum(1 for r in group if r.get("status") == "error")
        item = {"hour": hour, "total": len(group), "errors": e, "error_rate": rate(e, len(group))}
        if item["total"] >= 5 and item["error_rate"] >= 3 * error_rate and e > 0:
            out.append(item)
    return out


def slo(report_: dict, limits: dict | None = None) -> dict:
    """R7: a metric above its limit is a breach (equal is kept)."""
    limits = {**DEFAULT_SLO, **(limits or {})}
    breaches = [k for k in ("error_rate", "p95_ms", "unanswered_rate") if report_[k] > limits[k]]
    return {"ok": not breaches, "breaches": breaches, "limits": limits}


def report(rows: list[dict], limits: dict | None = None) -> dict:
    """Everything my-log-report returns, with the same names (R5)."""
    out = summary(rows)
    out.update(steps_and_cost(rows))
    out.update(problems(rows))
    out["anomalies"] = anomalies(rows, out["error_rate"])
    out["unanswered_rate"] = rate(sum(1 for r in rows if r.get("route") == "담당자 연결"), len(rows))
    out["slo"] = slo(out, limits)
    return out


def compare(now: dict, prev: dict) -> list[dict]:
    """R8: the main metrics side by side with the change."""
    rows = []
    for key in ("total", "errors", "error_rate", "p50_ms", "p95_ms", "unanswered_rate", "cost_usd"):
        a, b = prev.get(key, 0), now.get(key, 0)
        rows.append({"metric": key, "prev": a, "now": b, "change": round(b - a, 6)})
    return rows


def percent(value: float) -> str:
    return f"{round(value * 10000) / 100:g}%"


def weekly_markdown(now: dict, prev: dict, date_from: str, date_to: str) -> str:
    """R10: the weekly report of Lab 03 task 1 without the LLM: numbers and problems by Code, next actions by rules."""
    def slo_text(r: dict) -> str:
        return "지킴" if r["slo"]["ok"] else "못 지킴 " + ", ".join(r["slo"]["breaches"])

    lines = [f"# IT 헬프데스크 주간 운영 보고 ({date_from} ~ {date_to})", "", "## 숫자", "", "| 지표 | 지난주 | 이번 주 |", "| --- | --- | --- |",
             f"| 요청 | {prev['total']} | {now['total']} |", f"| 오류율 | {percent(prev['error_rate'])} | {percent(now['error_rate'])} |",
             f"| p95 | {prev['p95_ms']}ms | {now['p95_ms']}ms |",
             f"| 답 못 함 | {percent(prev['unanswered_rate'])} | {percent(now['unanswered_rate'])} |",
             f"| SLO | {slo_text(prev)} | {slo_text(now)} |", "", "## 문제", ""]
    for f in now["failures"][:3]:
        lines.append(f"- 실패 {f['count']}건 · {f['node']} · {f['message']}")
    for u in now["unanswered_topics"][:3]:
        lines.append(f"- 답하지 못한 질문 {u['count']}건 · {u['topic']}")
    for a in now["anomalies"]:
        lines.append(f"- 이상 시간대 {a['hour'][:10]} {a['hour'][11:13]}시 · {a['errors']}/{a['total']} 실패")
    lines += ["", "## 다음 할 일", ""]
    if now["unanswered_topics"]:
        lines.append(f"- FAQ에 '{now['unanswered_topics'][0]['topic']}' 항목 추가")
    if any(f["node"] == "Search FAQ" for f in now["failures"]):
        lines.append("- FAQ 검색 timeout · 재시도 설정 점검 (72일차)")
    if any("429" in str(f["message"]) for f in now["failures"]):
        lines.append("- LLM 사용량 한도 · 대체 경로 점검 (75 · 72일차)")
    return "\n".join(lines) + "\n"
