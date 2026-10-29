"""Command line. Exit codes: diff 0 same · 1 different, 2 error (any command)."""
import argparse
import json
import sys
from pathlib import Path

from . import diff
from .store import DEFAULT_REPO, Store, StoreError, export_from_n8n, safe_name
from .workflow import NotWorkflow, load

COMMANDS = ("diff", "save", "log", "show", "restore", "pull")


def load_side(store: Store, spec: str, name: str | None) -> dict:
    """A file path, or a revision of <name> in the store."""
    if Path(spec).exists():
        return load(spec)
    if not name:
        raise StoreError(f"{spec}: no such file (to compare versions give the workflow name: tver diff <rev1> <rev2> <name>)")
    return store.show(spec, name)


def print_changes(changes, full=False):
    for change in changes:
        print(change.title())
        if change.lines and full:
            for row in change.lines:
                print(f"    {row}")
    print(diff.summary_line(diff.summary(changes)))


def run_diff(args, store):
    old = load_side(store, args.old, args.name)
    new = load_side(store, args.new, args.name)
    changes = diff.compare(old, new)
    if args.json:
        print(json.dumps({"changes": [c.to_dict() for c in changes], "summary": diff.summary(changes)},
                         ensure_ascii=False, indent=2))
    else:
        print(f"{old.get('name', args.old)}  →  {new.get('name', args.new)}")
        print_changes(changes, full=not args.short)
    return 1 if changes else 0


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if argv and argv[0] not in COMMANDS and not argv[0].startswith("-"):
        from .app import VersionApp  # `tver <workflow file or name>` opens the TUI
        repo = None
        if "--repo" in argv:
            repo = argv[argv.index("--repo") + 1]
        VersionApp(argv[0], Store(repo)).run()
        sys.exit(0)
    p = argparse.ArgumentParser(prog="tver", description="n8n workflow versions in git, compared node by node. "
                                "`tver <file or name>` opens the TUI.")
    p.add_argument("--repo", default=None, help=f"version store (default {DEFAULT_REPO}, or $TVER_REPO)")
    sub = p.add_subparsers(dest="cmd", required=True)
    d = sub.add_parser("diff", help="compare two files, or two versions: tver diff <rev1> <rev2> <name>")
    d.add_argument("old")
    d.add_argument("new")
    d.add_argument("name", nargs="?", help="workflow name in the store when old/new are revisions")
    d.add_argument("--plain", action="store_true", help="plain lines (default)")
    d.add_argument("--short", action="store_true", help="no line diff for long text")
    d.add_argument("--json", action="store_true", help="JSON for other programs")
    s = sub.add_parser("save", help="save a workflow file (or every workflow file in a folder) as a new version")
    s.add_argument("path")
    s.add_argument("--allow-secrets", action="store_true", help="save even if it looks like it has a secret (not advised)")
    lg = sub.add_parser("log", help="versions of one workflow")
    lg.add_argument("name")
    lg.add_argument("--json", action="store_true")
    sh = sub.add_parser("show", help="print one version")
    sh.add_argument("rev")
    sh.add_argument("name")
    r = sub.add_parser("restore", help="write an old version to a file (then push it yourself)")
    r.add_argument("rev")
    r.add_argument("name")
    r.add_argument("-o", "--out", required=True, help="file to write, e.g. my-work/helpdesk.json")
    pl = sub.add_parser("pull", help="export every workflow from the running n8n and save each as a version")
    pl.add_argument("--container", default="day65-n8n-n8n-1")
    args = p.parse_args(argv)
    store = Store(args.repo)
    try:
        if args.cmd == "diff":
            return run_diff(args, store)
        if args.cmd == "save":
            rows = store.save(args.path, args.allow_secrets)
            for name, status, message in rows:
                print(f"{status:9} {name}" + (f"  {message}" if message and status == "saved" else ""))
            return 0
        if args.cmd == "log":
            versions = store.log(args.name)
            if args.json:
                print(json.dumps([v.__dict__ for v in versions], ensure_ascii=False, indent=2))
            for v in versions if not args.json else []:
                print(f"{v.rev}  {v.date}  {v.message}")
            if not versions:
                print(f"no versions of {safe_name(Path(args.name).name)} in {store.repo}", file=sys.stderr)
            return 0
        if args.cmd == "show":
            print(json.dumps(store.show(args.rev, args.name), ensure_ascii=False, indent=2))
            return 0
        if args.cmd == "restore":
            out = store.restore(args.rev, args.name, args.out)
            print(f"wrote {out} from {args.rev}. Push it yourself: uv run tools/flow.py push {out}")
            return 0
        if args.cmd == "pull":
            saved = 0
            for workflow in export_from_n8n(args.container):
                status, message = store.save_workflow(workflow, safe_name(str(workflow.get("name", "workflow"))))
                saved += status == "saved"
                print(f"{status:9} {safe_name(str(workflow.get('name')))}" + (f"  {message}" if status == "saved" else ""))
            print(f"{saved} new version(s) in {store.repo}")
            return 0
    except (StoreError, NotWorkflow) as error:
        print(f"tver: {error}", file=sys.stderr)
        return 2
    return 2


if __name__ == "__main__":
    sys.exit(main())
