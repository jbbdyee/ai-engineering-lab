"""git: staged content (R5), pre-commit hook (R6), past commits (R9)."""
import stat
import subprocess
from pathlib import Path

from .files import env_values_from, is_env_file, scan_items

MARK = "# tscan pre-commit hook"
HOOK = f"#!/bin/sh\n{MARK} (remove with: tscan uninstall-hook)\nexec tscan staged\n"


def git(root, *args):
    return subprocess.run(["git", "-C", str(root), *args], capture_output=True, check=True).stdout


def top(root):
    return Path(git(root, "rev-parse", "--show-toplevel").decode().strip())


def staged(root):
    """Scan what `git add` put in the index, not the working file."""
    root = top(root)
    names = [n for n in git(root, "diff", "--cached", "--name-only", "--diff-filter=ACM", "-z").decode().split("\0") if n]
    items, env_values = [], set()
    for name in names:
        data = git(root, "show", f":{name}")
        if b"\0" in data[:8192] or len(data) > 1_000_000:
            continue
        text = data.decode("utf-8", errors="replace")
        items.append((name, text))
        if is_env_file(Path(name).name):
            env_values |= env_values_from(text)
    return scan_items(items, root, sorted(env_values, key=len, reverse=True)), {"files": len(items)}


def hook_path(root):
    return top(root) / Path(git(root, "rev-parse", "--git-path", "hooks").decode().strip()) / "pre-commit"


def install_hook(root):
    p = hook_path(root)
    if p.exists() and MARK not in p.read_text(errors="replace"):
        return False, f"{p} already exists and is not a tscan hook; add 'tscan staged' to it yourself"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(HOOK)
    p.chmod(p.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return True, f"installed {p}"


def uninstall_hook(root):
    p = hook_path(root)
    if not p.exists():
        return True, "no pre-commit hook"
    if MARK not in p.read_text(errors="replace"):
        return False, f"{p} is not a tscan hook; left as is"
    p.unlink()
    return True, f"removed {p}"


def history(root, max_commits=200):
    """Lines added in past commits. Each finding's path is '<short commit> <file>'."""
    root = top(root)
    log = git(root, "log", f"-{max_commits}", "-p", "--no-color", "--format=commit %h").decode("utf-8", errors="replace")
    items, commit, path, lines = [], "", "", []

    def flush():
        if path and lines:
            items.append((f"{commit} {path}", "\n".join(lines)))

    for row in log.splitlines():
        if row.startswith("commit "):
            flush()
            commit, path, lines = row.split()[1], "", []
        elif row.startswith("+++ "):
            flush()
            path, lines = row[6:] if row.startswith("+++ b/") else "", []
        elif row.startswith("+") and path:
            lines.append(row[1:])
    flush()
    return scan_items(items, root), {"commits": max_commits}
