"""What to show (R1 · R7 · R8): the colors and numbers come from the facts as they are; nothing is recounted here."""
from __future__ import annotations

import json
import shutil
import subprocess

AREAS = ("runs", "alerts", "dlq", "quality", "cost", "release")
LABEL = {"runs": "runs", "alerts": "alerts", "dlq": "DLQ", "quality": "quality", "cost": "cost", "release": "release"}
MARK = {"red": "🔴", "yellow": "🟡", "green": "🟢", "unknown": "⚪"}


def pct(value) -> str:
    return f"{round(value * 100, 2)}%"


def numbers(f: dict, area: str) -> str:
    """The same short form as the day 79 brief table (AGENTS.md 3)."""
    x = f.get(area)
    if x is None:
        return "source not answering"
    if area == "runs":
        return f"error rate {pct(x['error_rate'])} · p95 {x['p95_ms']}ms · unanswered {pct(x['unanswered_rate'])}"
    if area == "alerts":
        return f"{x['count']} (high {x['high']})"
    if area == "dlq":
        return f"{x['size']} (parked {x['parked']})"
    if area == "quality":
        return f"avg {x['avg_score']} · last {x['last_score']} · quarantine {x['quarantine']}"
    if area == "cost":
        return f"${x['cost_usd']} / ${x['daily_usd']} ({pct(x['used_ratio'])})"
    text = str(x["active"])
    if x.get("canary_release"):
        rate = "-" if x.get("canary_repeat_rate") is None else pct(x["canary_repeat_rate"])
        text += f" · canary {x['canary_release']} {x['canary_percent']}% (repeat {rate})"
    return text


def status_lines(f: dict) -> list[str]:
    period = f.get("period", {})
    lines = [f"overall {MARK.get(f['overall'], '?')} {f['overall']} · runs {period.get('from', '…')} ~ {period.get('to', '…')} + state now"]
    for area in AREAS:
        color = f["health"].get(area, "unknown")
        lines.append(f"  {MARK.get(color, '?')} {LABEL[area]:<8} {numbers(f, area)}")
    if f.get("sources_down"):
        lines.append("  sources down: " + ", ".join(f["sources_down"]))
    return lines


def answer_lines(a: dict) -> list[str]:
    head = f"[{a.get('area')} · {a.get('router')}]"
    if a.get("refused"):
        return [f"{head} refused ({a.get('reason')})", f"  {a.get('answer')}"]
    check = "numbers ✔" if a.get("numbers_ok") else f"numbers ✘ {a.get('unknown_numbers')}"
    return [f"{head} {check}", f"  {a.get('answer')}"]


def tool(name: str, args: list[str], timeout: float = 30) -> dict:
    """R8: an earlier course tool as a part (its --json), or why it is not available."""
    if not shutil.which(name):
        return {"tool": name, "ok": False, "why": "not installed (uv tool install)"}
    try:
        out = subprocess.run([name, *args], capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return {"tool": name, "ok": False, "why": "timed out"}
    try:
        return {"tool": name, "ok": True, "code": out.returncode, "result": json.loads(out.stdout)}
    except json.JSONDecodeError:
        if out.returncode == 0:
            return {"tool": name, "ok": True, "code": 0, "result": out.stdout.strip().splitlines()[-1:]}
        return {"tool": name, "ok": False, "why": (out.stderr or out.stdout).strip().splitlines()[-1][:120] if (out.stderr or out.stdout).strip() else f"exit {out.returncode}"}


def tool_line(part: dict) -> str:
    """tlog slo → its breaches (the day 77 SLO, its own definition); any other tool → installed."""
    if not part["ok"]:
        return f"  · {part['tool']}: {part['why']}"
    r = part["result"]
    if part["tool"] == "tlog" and isinstance(r, dict):
        return f"  ✔ tlog slo: {'ok' if r.get('ok') else 'breaches ' + ', '.join(r.get('breaches', []))} ({r.get('total')} runs)"
    return f"  ✔ {part['tool']}: installed"
