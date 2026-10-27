"""Walk a folder: text files only, with .env values, ignore list and user rules."""
import fnmatch
import os
import tomllib
from pathlib import Path

from .scanner import compile_rules, scan_text

SKIP_DIRS = {".git", "node_modules", ".venv", "venv", "__pycache__", ".mypy_cache", ".pytest_cache", ".tox"}
MAX_BYTES = 1_000_000
IGNORE_FILE = ".tscanignore"


def home():
    return Path(os.environ.get("TSCAN_HOME", Path.home() / ".tscan"))


def read_text(path):
    """Return (text, None) or (None, reason) for big or binary files."""
    try:
        size = path.stat().st_size
        if size > MAX_BYTES:
            return None, "too_big"
        data = path.read_bytes()
    except OSError:
        return None, "unreadable"
    if b"\0" in data[:8192]:
        return None, "binary"
    return data.decode("utf-8", errors="replace"), None


def is_env_file(name):
    return name == ".env" or (name.startswith(".env.") and not name.endswith((".example", ".sample", ".template")))


def env_values_from(text, min_len=6):
    values = set()
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        value = line.split("=", 1)[1].strip().strip("'\"")
        if len(value) >= min_len:
            values.add(value)
    return values


def load_rules(root):
    """User rules from ~/.tscan/rules.toml and <root>/.tscan.toml: [[rule]] name = ..., pattern = ... (R11)."""
    extra = []
    for p in (home() / "rules.toml", Path(root) / ".tscan.toml"):
        if p.is_file():
            extra += tomllib.loads(p.read_text(encoding="utf-8")).get("rule", [])
    return compile_rules(extra)


def load_ignore(root):
    p = Path(root) / IGNORE_FILE
    if not p.is_file():
        return []
    return [line.strip() for line in p.read_text(encoding="utf-8").splitlines() if line.strip() and not line.startswith("#")]


def ignored(finding, entries):
    """Entries: 'path:line', 'kind:path' or a path glob (R7)."""
    for entry in entries:
        head, _, tail = entry.rpartition(":")
        if head and tail.isdigit() and head == finding.path and int(tail) == finding.line:
            return True
        if head and not tail.isdigit() and head == finding.kind and fnmatch.fnmatch(finding.path, tail):
            return True
        if not head and fnmatch.fnmatch(finding.path, entry):
            return True
    return False


def add_ignore(root, entry):
    p = Path(root) / IGNORE_FILE
    with p.open("a", encoding="utf-8") as f:
        f.write(entry + "\n")
    return p


def iter_files(root):
    root = Path(root)
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS)
        for name in sorted(filenames):
            yield Path(dirpath) / name


def scan_items(items, root, env_values=()):
    """items: (relative path, text). Shared by folder, staged and history scans."""
    rules = load_rules(root)
    entries = load_ignore(root)
    found = []
    for rel, text in items:
        values = () if is_env_file(Path(rel).name) else env_values
        found += [f for f in scan_text(text, rel, rules, values) if not ignored(f, entries)]
    return found


def scan_folder(root):
    """Return (findings, report) where report has files, skipped (by reason)."""
    root = Path(root)
    texts, skipped, env_values = [], {}, set()
    for path in iter_files(root):
        text, reason = read_text(path)
        if reason:
            skipped[reason] = skipped.get(reason, 0) + 1
            continue
        rel = path.relative_to(root).as_posix()
        texts.append((rel, text))
        if is_env_file(path.name):
            env_values |= env_values_from(text)
    found = scan_items(texts, root, sorted(env_values, key=len, reverse=True))
    return found, {"files": len(texts), "skipped": skipped}
