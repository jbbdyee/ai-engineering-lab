"""Command line. Exit codes: 0 nothing found, 1 found, 2 error."""
import argparse
import json
import subprocess
import sys
from collections import Counter

from . import gitscan
from .files import scan_folder


def summary(found, report):
    return {"total": len(found), "by_kind": dict(Counter(f.kind for f in found)),
            "by_file": dict(Counter(f.path for f in found)), **report}


def print_plain(found, report, with_summary):
    for f in found:
        print(f"{f.kind:13} {f.path}:{f.line}  {f.masked}")
    s = summary(found, report)
    skipped = sum(report.get("skipped", {}).values())
    print(f"found {s['total']} in {report.get('files', 0)} file(s)" + (f", skipped {skipped}" if "skipped" in report else ""))
    if with_summary:
        print("by kind  " + "  ".join(f"{k} {v}" for k, v in sorted(s["by_kind"].items())))
        for path, count in sorted(s["by_file"].items(), key=lambda kv: -kv[1]):
            print(f"  {count:3}  {path}")
        if report.get("skipped"):
            print("skipped  " + "  ".join(f"{k} {v}" for k, v in sorted(report["skipped"].items())))


def emit(found, report, args):
    if getattr(args, "json", False):
        print(json.dumps({"findings": [f.to_dict() for f in found], "summary": summary(found, report)}, ensure_ascii=False, indent=2))
    else:
        print_plain(found, report, getattr(args, "summary", False))
    return 1 if found else 0


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    commands = ("scan", "staged", "install-hook", "uninstall-hook", "history")
    if argv and argv[0] not in commands and not argv[0].startswith("-"):
        from .app import ScanApp  # `tscan <folder>` opens the TUI
        ScanApp(argv[0]).run()
        sys.exit(0)
    p = argparse.ArgumentParser(prog="tscan", description="Find secrets and personal data, shown masked. "
                                "`tscan <folder>` opens the TUI.")
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("scan", help="scan a folder")
    s.add_argument("folder")
    for q in (s, sub.add_parser("staged", help="scan staged files (for pre-commit)"),
              sub.add_parser("history", help="scan lines added in past commits")):
        q.add_argument("--plain", action="store_true", help="plain lines (default)")
        q.add_argument("--json", action="store_true", help="JSON for other programs (values masked)")
        q.add_argument("--summary", action="store_true", help="counts by kind and file, skipped files")
    sub.choices["history"].add_argument("--max", type=int, default=200, help="commits to read (default 200)")
    sub.add_parser("install-hook", help="run `tscan staged` before every commit in this repository")
    sub.add_parser("uninstall-hook", help="remove the tscan pre-commit hook")
    args = p.parse_args(argv)
    try:
        if args.cmd == "scan":
            found, report = scan_folder(args.folder)
        elif args.cmd == "staged":
            found, report = gitscan.staged(".")
            if found and not args.json:
                print("tscan: secrets or personal data in staged files; commit stopped", file=sys.stderr)
        elif args.cmd == "history":
            found, report = gitscan.history(".", args.max)
        else:
            ok, message = (gitscan.install_hook if args.cmd == "install-hook" else gitscan.uninstall_hook)(".")
            print(message)
            sys.exit(0 if ok else 2)
        sys.exit(emit(found, report, args))
    except (subprocess.CalledProcessError, FileNotFoundError, OSError) as error:
        print(f"tscan: {error.__class__.__name__}: not a git repository or unreadable path", file=sys.stderr)
        sys.exit(2)
