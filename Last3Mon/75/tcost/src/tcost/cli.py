"""Command line. Exit codes: 0 fine · 1 a cost is over --max-usd · 2 error (no file, unknown model, bad price table)."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import prices as price_table
from . import tokens
from .prices import UnknownModel
from .scan import TEXT, scan
from .usage import collect
from .workflow import NotWorkflow, llm_steps, load

COMMANDS = ("count", "workflow", "usage", "compare", "budget", "scan")


def money(value: float) -> str:
    return f"${value:.6f}" if value < 1 else f"${value:,.2f}"


def text_files(paths: list[str]) -> list[Path]:
    files: list[Path] = []
    for path in map(Path, paths):
        if path.is_dir():
            files += scan(path).texts
        elif path.exists():
            files.append(path)
        else:
            raise FileNotFoundError(f"{path}: no such file")
    return files


def warn(prices) -> None:
    if message := prices.warning():
        print(f"! {message}", file=sys.stderr)


def run_count(args, prices) -> int:
    """R1 · R2: tokens of each file, and what one call / 1,000 calls cost on each model (input + --out tokens)."""
    models = args.model or sorted(prices.models)
    rows = []
    for path in text_files(args.files):
        n = tokens.count(path.read_text(encoding="utf-8"))
        rows.append({"file": str(path), "tokens": n, "out": args.out,
                     "cost": {m: prices.cost(m, n, args.out) for m in models}})
    return show_rows(args, rows, models, "file", prices)


def run_workflow(args, prices) -> int:
    """R4: each LLM step of a workflow, the fixed system prompt it sends, and that part's cost per call."""
    models: set[str] = set()
    rows = []
    for path in map(Path, args.files):
        files = scan(path).workflows if path.is_dir() else [path]
        for file in files:
            for step in llm_steps(load(file)):
                out = step.max_out if args.out is None else args.out
                cost = prices.cost(step.model, step.system_tokens, out or 0)
                models.add(step.model)
                rows.append({"file": file.name, "node": step.node, "model": step.model, "tokens": step.system_tokens,
                             "out": out or 0, "dynamic": step.dynamic, "cost": {step.model: cost}})
    if args.json:
        print(json.dumps({"steps": rows, "prices_checked": prices.checked}, ensure_ascii=False, indent=2))
        return over(args, rows)
    print(f"{'file':<34} {'node':<16} {'model':<13} {'system':>7} {'out':>5} {'per call':>11} {'per 1,000':>10}")
    for row in rows:
        cost = row["cost"][row["model"]]
        note = "  (built at run time)" if row["dynamic"] else ""
        print(f"{row['file'][:34]:<34} {row['node'][:16]:<16} {row['model']:<13} {row['tokens']:>7} {row['out']:>5}"
              f" {money(cost):>11} {money(cost * 1000):>10}{note}")
    print("system prompts only: questions, FAQ and ticket data are added at run time (see `tcost usage`).")
    return over(args, rows)


def show_rows(args, rows, models, label, prices) -> int:
    if args.json:
        print(json.dumps({"rows": rows, "prices_checked": prices.checked}, ensure_ascii=False, indent=2))
        return over(args, rows)
    head = "".join(f" {m + ' /call':>20} {'/1,000':>10}" for m in models)
    print(f"{label:<40} {'tokens':>7} {'out':>5}{head}")
    for row in rows:
        cells = "".join(f" {money(row['cost'][m]):>20} {money(row['cost'][m] * 1000):>10}" for m in models)
        print(f"{row[label][-40:]:<40} {row['tokens']:>7} {row['out']:>5}{cells}")
    return over(args, rows)


def over(args, rows) -> int:
    """R10: exit 1 when any one call costs more than --max-usd (a cost gate before deploying)."""
    if args.max_usd is None:
        return 0
    worst = max((cost for row in rows for cost in row["cost"].values()), default=0.0)
    if worst > args.max_usd:
        print(f"✘ one call costs up to {money(worst)} (more than --max-usd {money(args.max_usd)})", file=sys.stderr)
        return 1
    print(f"✔ every call is at most {money(args.max_usd)}", file=sys.stderr)
    return 0


def run_usage(args, prices) -> int:
    """R5 · R6: what the test reports really used, and a month at --per-day requests."""
    usage = collect(args.paths)
    if args.json:
        data = usage.to_dict()
        if args.per_day:
            data["month_usd"] = usage.month(args.per_day, args.days)
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return 0
    t = usage.total
    print(f"{usage.reports} report(s) · {usage.requests} request(s) · {t['calls']} call(s) · tokens in {t['prompt_tokens']}"
          f" / out {t['completion_tokens']} · {money(t['cost_usd'])} · avg {money(usage.avg_usd)} per request"
          f" · skipped {usage.skipped} (no usage)")
    for title, table in (("model", usage.by_model), ("user", usage.by_user), ("hour", usage.by_hour)):
        for key, row in sorted(table.items(), key=lambda kv: (-kv[1]["cost_usd"]) if title != "hour" else kv[0]):
            print(f"  {title:<6} {key:<14} {row['calls']:>5} calls · in {row['prompt_tokens']:>8} · out {row['completion_tokens']:>7}"
                  f" · {money(row['cost_usd'])}")
    if args.per_day:
        print(f"month: {money(usage.avg_usd)} × {args.per_day} a day × {args.days} days = {money(usage.month(args.per_day, args.days))}")
    return 0


def run_compare(args, prices) -> int:
    """R7: the same file on two (or more) models side by side, and how much the cheaper one saves."""
    if len(args.model or []) < 2:
        raise ValueError("compare needs two models: --model gpt-4.1-mini --model gpt-5.4-nano")
    n = tokens.count(Path(args.file).read_text(encoding="utf-8"))
    costs = {m: prices.cost(m, n, args.out) for m in args.model}
    base = costs[args.model[0]]
    if args.json:
        print(json.dumps({"file": args.file, "tokens": n, "out": args.out, "cost": costs}, ensure_ascii=False, indent=2))
        return 0
    print(f"{args.file}: {n} tokens in · {args.out} out")
    for model, cost in costs.items():
        pct = (base - cost) / base * 100 if base else 0
        saving = "" if model == args.model[0] or not base else \
            f"{abs(pct):.0f}% {'cheaper' if pct > 0 else 'dearer'} than {args.model[0]}"
        print(f"  {model:<14} per call {money(cost):>11} · per 1,000 {money(cost * 1000):>10}  {saving}")
    return 0


def run_budget(args, prices) -> int:
    """R9: how many calls of this file a daily budget pays for, on each model."""
    n = tokens.count(Path(args.file).read_text(encoding="utf-8"))
    rows = {m: prices.cost(m, n, args.out) for m in (args.model or sorted(prices.models))}
    if args.json:
        print(json.dumps({m: {"per_call": c, "calls": int(args.usd // c) if c else None} for m, c in rows.items()}, indent=2))
        return 0
    print(f"budget {money(args.usd)} a day · {args.file}: {n} tokens in · {args.out} out")
    for model, cost in rows.items():
        print(f"  {model:<14} {money(cost):>11} a call → {int(args.usd // cost) if cost else '∞':>8} call(s) a day")
    return 0


def run_scan(args, prices) -> int:
    found = scan(args.folder)
    for title, files in (("text", found.texts), ("workflow", found.workflows), ("report", found.reports), ("skipped", found.skipped)):
        print(f"{title:<9} {len(files):>4}  " + ", ".join(p.name for p in files[:6]) + (" …" if len(files) > 6 else ""))
    return 0


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if argv and argv[0] not in COMMANDS and not argv[0].startswith("-"):
        from .app import CostApp  # `tcost <folder> [folder ...]` opens the TUI
        prices = price_table.load(argv[argv.index("--prices") + 1] if "--prices" in argv else None)
        paths = argv[:argv.index("--prices")] if "--prices" in argv else argv
        CostApp(paths, prices).run()
        sys.exit(0)
    p = argparse.ArgumentParser(prog="tcost", description="Count tokens and estimate LLM cost before calling (no API call), "
                                "and sum the usage of n8n test reports. `tcost <folder> [folder ...]` opens the TUI.")
    p.add_argument("--prices", help="price table (default $TCOST_PRICES, ~/.tcost/prices.json, else the one shipped with tcost)")
    sub = p.add_subparsers(dest="cmd", required=True)

    def common(item, out_default=0):
        item.add_argument("--out", type=int, default=out_default, help="output tokens assumed per call")
        item.add_argument("--model", action="append", help="model name from the price table (repeat for more)")
        item.add_argument("--max-usd", type=float, help="exit 1 when one call costs more than this")
        item.add_argument("--json", action="store_true", help="JSON for other programs")

    item = sub.add_parser("count", help="tokens of text files and their cost on each model")
    item.add_argument("files", nargs="+", help="files or folders (.txt .prompt)")
    common(item)
    item = sub.add_parser("workflow", help="LLM steps of n8n workflows and the fixed prompt each sends")
    item.add_argument("files", nargs="+", help="workflow files or folders")
    common(item, None)
    item = sub.add_parser("usage", help="sum usage and cost_usd of flow.py test reports (runs/*.json)")
    item.add_argument("paths", nargs="+")
    item.add_argument("--per-day", type=int, help="requests a day, for a month projection")
    item.add_argument("--days", type=int, default=22, help="working days in a month (default 22)")
    item.add_argument("--json", action="store_true")
    item = sub.add_parser("compare", help="one file on two models side by side")
    item.add_argument("file")
    common(item)
    item = sub.add_parser("budget", help="how many calls a daily budget pays for")
    item.add_argument("usd", type=float)
    item.add_argument("file")
    common(item)
    item = sub.add_parser("scan", help="what tcost finds in a folder (texts, workflows, reports, skipped)")
    item.add_argument("folder")
    args = p.parse_args(argv)
    try:
        prices = price_table.load(args.prices)
        warn(prices)
        for model in getattr(args, "model", None) or []:
            prices.rate(model)               # R12: an unknown model name stops here, it is never priced as 0
        runner = {"count": run_count, "workflow": run_workflow, "usage": run_usage, "compare": run_compare,
                  "budget": run_budget, "scan": run_scan}[args.cmd]
        sys.exit(runner(args, prices))
    except (UnknownModel, FileNotFoundError, NotWorkflow, ValueError, json.JSONDecodeError) as error:
        print(f"✘ {error}", file=sys.stderr)
        sys.exit(2)
