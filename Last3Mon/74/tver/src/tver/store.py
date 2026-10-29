"""Versions in a git repository (R5 save · R6 log/show · R10 restore · R13 folder · R9 pull from n8n)."""
import json
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path

from . import diff
from .workflow import NotWorkflow, dumps, find_secrets, is_workflow, load, parse

DEFAULT_REPO = Path(os.getenv("TVER_REPO", Path.home() / ".tver" / "store"))


class StoreError(RuntimeError):
    pass


@dataclass
class Version:
    rev: str
    date: str
    message: str


def safe_name(name: str) -> str:
    keep = "".join(ch if ch.isalnum() or ch in "-_." else "-" for ch in name.strip())
    return (keep or "workflow").lower() + ("" if keep.endswith(".json") else ".json")


class Store:
    def __init__(self, repo=None):
        self.repo = Path(repo or DEFAULT_REPO).expanduser()

    def git(self, *args, check=True) -> str:
        result = subprocess.run(["git", "-C", str(self.repo), *args], capture_output=True, text=True)
        if check and result.returncode != 0:
            raise StoreError((result.stderr or result.stdout).strip() or f"git {args[0]} failed")
        return result.stdout

    def ensure(self):
        if not (self.repo / ".git").exists():
            self.repo.mkdir(parents=True, exist_ok=True)
            self.git("init", "-q")
            self.git("config", "user.name", "tver")
            self.git("config", "user.email", "tver@localhost")

    def save_workflow(self, workflow: dict, name: str, force_secrets=False) -> tuple[str, str]:
        """Write the cleaned JSON as <name> and commit when it changed. Returns (status, message)."""
        text = dumps(workflow)
        secrets = find_secrets(text)
        if secrets and not force_secrets:
            raise StoreError(f"{name}: looks like a secret ({', '.join(secrets)}). Not saved. "
                             "Remove it (use an n8n Credential) and save again.")
        self.ensure()
        target = self.repo / name
        previous = target.read_text(encoding="utf-8") if target.exists() else None
        if previous == text:
            return "no change", ""
        message = f"{name}: new" if previous is None else \
            f"{name}: " + diff.summary_line(diff.summary(diff.compare(parse(previous, name), parse(text, name))))
        target.write_text(text, encoding="utf-8")
        self.git("add", name)
        self.git("commit", "-q", "-m", message)
        return "saved", message

    def save(self, path, force_secrets=False) -> list[tuple[str, str, str]]:
        """A file, or every workflow file in a folder (others are skipped). Returns (name, status, message)."""
        path = Path(path)
        files = sorted(path.glob("*.json")) if path.is_dir() else [path]
        out = []
        for file in files:
            try:
                workflow = load(file)
            except NotWorkflow:
                if path.is_dir():
                    out.append((file.name, "skipped", "not a workflow"))
                    continue
                raise
            status, message = self.save_workflow(workflow, safe_name(file.name), force_secrets)
            out.append((safe_name(file.name), status, message))
        return out

    def names(self) -> list[str]:
        if not (self.repo / ".git").exists():
            return []
        return sorted(line for line in self.git("ls-files").splitlines() if line.endswith(".json"))

    def log(self, name: str) -> list[Version]:
        name = safe_name(Path(name).name)
        if not (self.repo / ".git").exists():
            return []
        rows = self.git("log", "--format=%h%x09%ad%x09%s", "--date=format:%Y-%m-%d %H:%M:%S", "--", name, check=False)
        return [Version(*row.split("\t", 2)) for row in rows.splitlines() if row.count("\t") >= 2]

    def show(self, rev: str, name: str) -> dict:
        name = safe_name(Path(name).name)
        return parse(self.git("show", f"{rev}:{name}"), f"{rev}:{name}")

    def restore(self, rev: str, name: str, out) -> Path:
        """Write that version to a file (the person pushes it to n8n). The store itself is not changed."""
        workflow = self.show(rev, name)
        out = Path(out)
        out.write_text(json.dumps(workflow, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return out


def export_from_n8n(container: str) -> list[dict]:
    """R9: every workflow in the running n8n container (docker exec ... n8n export:workflow --all)."""
    command = ["docker", "exec", container, "sh", "-c",
               "n8n export:workflow --all --output=/tmp/tver-all.json >/dev/null 2>&1; cat /tmp/tver-all.json; rm -f /tmp/tver-all.json"]
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=120)
    except (OSError, subprocess.TimeoutExpired) as error:
        raise StoreError(f"docker exec failed: {error}") from error
    if result.returncode != 0 or not result.stdout.strip():
        raise StoreError((result.stderr or "no output").strip() + f"\n  Is the n8n container '{container}' running?")
    data = json.loads(result.stdout)
    return [item for item in (data if isinstance(data, list) else [data]) if is_workflow(item)]
