"""Command line. Exit codes: 0 worked (maybe by the fallback) · 1 all tries and the fallback failed ·
2 usage error · 3 not retryable (e.g. HTTP 400: the request itself is wrong)."""
from __future__ import annotations

import argparse
import json
import shlex
import sys
import uuid
from pathlib import Path

from . import log, runners
from .retry import Policy, Result, run_with_retry

SUBCOMMANDS = ("http", "stats", "log")


def options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--tries", type=int, default=3, help="how many tries (default 3)")
    parser.add_argument("--backoff", type=float, default=0.5, help="wait before try 2, doubled each time (default 0.5s)")
    parser.add_argument("--max-wait", type=float, default=8.0, help="longest single wait (default 8s)")
    parser.add_argument("--jitter", type=float, default=0.0, help="make each wait up to this share shorter, e.g. 0.2")
    parser.add_argument("--timeout", type=float, help="seconds for one try")
    parser.add_argument("--deadline", type=float, help="seconds for all tries together")
    parser.add_argument("--fallback", help='shell command to run once when every try failed, e.g. "cat cached.json"')
    parser.add_argument("--breaker", type=int, default=5,
                        help="skip straight to the fallback when the last N tries at this target in 60s all failed (0 = off)")
    parser.add_argument("--log", type=Path, help="log file (default $TRETRY_LOG or ~/.tretry/log.jsonl)")
    parser.add_argument("--json", action="store_true", help="print the result as JSON for other programs")
    parser.add_argument("-q", "--quiet", action="store_true", help="print only the output of the command that worked")


def policy(args) -> Policy:
    if args.tries < 1 or args.backoff < 0 or args.max_wait < 0 or not 0 <= args.jitter < 1:
        raise SystemExit(usage_error("--tries must be ≥ 1, --backoff/--max-wait ≥ 0, --jitter in [0, 1)"))
    return Policy(args.tries, args.backoff, args.max_wait, args.jitter, args.deadline)


def usage_error(message: str) -> int:
    print(f"tretry: {message}", file=sys.stderr)
    return 2


def report(args, kind: str, target: str, result: Result, path: Path) -> int:
    log.write(path, kind, target, result)
    code = 0 if result.ok else (3 if result.stopped == "not-retryable" else 1)
    if args.json:
        print(json.dumps({"ok": result.ok, "exit_code": code, "stopped": result.stopped, "used_fallback": result.used_fallback,
                          "seconds": result.seconds, "attempts": [a.__dict__ for a in result.attempts], "output": result.output},
                         ensure_ascii=False, indent=2))
        return code
    if not args.quiet:
        for a in result.attempts:
            mark = "✔" if a.ok else "✘"
            label = "fallback" if a.fallback else f"#{a.attempt}"
            wait = f" (waited {a.waited:.2f}s)" if a.waited else ""
            print(f"{label:<9}{a.started:>7.2f}s  {mark} {a.error or 'ok'} · {a.seconds:.2f}s{wait}", file=sys.stderr)
        how = "by the fallback" if result.ok and result.used_fallback else ("" if result.ok else f"({result.stopped})")
        tries = sum(1 for a in result.attempts if not a.fallback)
        state = " ".join(part for part in ("ok" if result.ok else "FAILED", how) if part)
        print(f"result: {state} · {tries} tr{'y' if tries == 1 else 'ies'} · {result.seconds:.2f}s"
              + (" · breaker open: tries skipped" if result.stopped == "breaker" else ""), file=sys.stderr)
    if result.output:
        sys.stdout.write(result.output if result.output.endswith("\n") else result.output + "\n")
    return code


def run(args, kind: str, target: str, attempt) -> int:
    path = args.log or log.default_path()
    skip = args.breaker > 0 and log.breaker_open(log.read(path), target, failures=args.breaker)
    if skip and not args.fallback:
        print(f"tretry: breaker open for {log.clean(target)} (last {args.breaker} tries failed); no --fallback, so stopping",
              file=sys.stderr)
    fallback = runners.command(args.fallback, shell=True) if args.fallback else None
    result = run_with_retry(attempt, policy(args), fallback=fallback, per_try_timeout=args.timeout, skip_tries=skip)
    return report(args, kind, target, result, path)


def main_command(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="tretry", usage="tretry [options] -- <command ...>",
                                     description="Run a command with timeout, retry (backoff), deadline and fallback.",
                                     epilog="also: tretry http METHOD URL · tretry stats · tretry log (screen)")
    options(parser)
    if "--" not in argv:
        if "-h" in argv or "--help" in argv:
            parser.print_help()
            return 0
        return usage_error("put the command after --, e.g. tretry --tries 3 -- curl -sf http://localhost:8800/health")
    split = argv.index("--")
    args = parser.parse_args(argv[:split])
    command = argv[split + 1:]
    if not command:
        return usage_error("no command after --")
    return run(args, "command", shlex.join(command), runners.command(command))


def main_http(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="tretry http", description="HTTP call: 5xx, 408/425/429, timeout and connection errors are "
                                                                     "tried again; other 4xx are not.")
    parser.add_argument("method")
    parser.add_argument("url")
    parser.add_argument("--body", help="JSON body, or @file.json")
    parser.add_argument("--header", action="append", default=[], help="K: V (values are never logged)")
    parser.add_argument("--idem-key", help="idempotency key sent with every try (header Idempotency-Key); 'auto' makes one")
    parser.add_argument("--body-key", help="also put the idempotency key in this JSON body field if it is missing, e.g. key")
    options(parser)
    args = parser.parse_args(argv)
    body = args.body
    if body and body.startswith("@"):
        body = Path(body[1:]).read_text(encoding="utf-8")
    if body:
        try:
            json.loads(body)
        except json.JSONDecodeError as error:
            return usage_error(f"--body is not JSON: {error}")
    headers = {}
    for item in args.header:
        name, _, value = item.partition(":")
        headers[name.strip()] = value.strip()
    key = uuid.uuid4().hex if args.idem_key == "auto" else args.idem_key
    if args.body_key and not key:
        return usage_error("--body-key needs --idem-key")
    target = f"{args.method.upper()} {args.url}"
    return run(args, "http", target, runners.http(args.method, args.url, body, headers, key, args.body_key))


def main_stats(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="tretry stats", description="Per target: runs, success rate, tries per run, p95 time.")
    parser.add_argument("--log", type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    rows = log.stats(log.read(args.log or log.default_path()))
    if args.json:
        print(json.dumps(rows, ensure_ascii=False, indent=2))
        return 0
    if not rows:
        print("no log yet")
        return 0
    print(f"{'target':<48} {'runs':>4} {'ok%':>5} {'tries/run':>9} {'failed':>6} {'fallback':>8} {'p95 s':>7}")
    for r in rows:
        print(f"{r['target'][:48]:<48} {r['runs']:>4} {r['success_rate'] * 100:>4.0f}% {r['attempts_per_run']:>9} "
              f"{r['failed_attempts']:>6} {r['fallbacks']:>8} {r['p95_seconds']:>7.2f}")
    return 0


def main_log(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="tretry log", description="Screen: targets by failures, and the tries of one target.")
    parser.add_argument("--log", type=Path)
    args = parser.parse_args(argv)
    from .app import LogApp
    LogApp(args.log or log.default_path()).run()
    return 0


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    try:
        if argv and argv[0] in SUBCOMMANDS:
            return {"http": main_http, "stats": main_stats, "log": main_log}[argv[0]](argv[1:])
        return main_command(argv)
    except SystemExit as stop:
        return stop.code if isinstance(stop.code, int) else 2


if __name__ == "__main__":
    sys.exit(main())
