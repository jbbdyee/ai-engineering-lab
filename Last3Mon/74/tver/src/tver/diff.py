"""Node-by-node difference of two workflows (R1), line diff for long text (R3),
model · prompt · flow summary (R4), renamed nodes (R12)."""
import difflib
import json
from dataclasses import asdict, dataclass, field

from .workflow import NOISE

LONG = 80
PROMPT_KEYS = ("systemMessage", "text", "jsCode", "pythonCode", "prompt")


@dataclass
class Change:
    op: str            # "+node" "-node" "~set" "renamed" "+link" "-link"
    node: str
    category: str      # "model" | "prompt" | "flow"
    key: str = ""
    before: object = None
    after: object = None
    lines: list = field(default_factory=list)   # unified diff lines for long text

    def to_dict(self):
        return asdict(self)

    def title(self):
        if self.op == "+node":
            return f"+ node '{self.node}' ({self.after})"
        if self.op == "-node":
            return f"- node '{self.node}' ({self.before})"
        if self.op == "renamed":
            return f"~ renamed '{self.before}' → '{self.after}'"
        if self.op in ("+link", "-link"):
            return f"{self.op[0]} link {self.node} → {self.after if self.op == '+link' else self.before} ({self.key})"
        if self.lines:
            return f"~ '{self.node}' {self.key}: changed ({len(text(self.before))} → {len(text(self.after))} chars)"
        return f"~ '{self.node}' {self.key}: {short(self.before)} → {short(self.after)}"


def text(value) -> str:
    if value is None:
        return "(none)"
    return value if isinstance(value, str) else json.dumps(value, ensure_ascii=False, sort_keys=True)


def short(value, width=60) -> str:
    s = text(value)
    return s if len(s) <= width else s[: width - 1] + "…"


def flat(value, prefix=""):
    if isinstance(value, dict) and value:
        out = {}
        for key, item in value.items():
            out.update(flat(item, f"{prefix}.{key}" if prefix else str(key)))
        return out
    return {prefix: value}


def kind(node) -> str:
    return str(node.get("type", "?")).split(".")[-1]


def category(node, key: str) -> str:
    """Chat model's model → model; Agent / chain text · systemMessage and Code → prompt; the rest → flow."""
    t = kind(node).lower()
    last = key.split(".")[-1]
    if t.startswith("lmchat") or t.startswith("lm") or "embeddings" in t:
        if last in ("model", "value", "modelName") and ("model" in key):
            return "model"
    if last in PROMPT_KEYS:
        return "prompt"
    return "flow"


def node_settings(node) -> dict:
    body = {k: v for k, v in node.items() if k not in NOISE and k != "name"}
    return flat(body)


def links(workflow) -> set:
    out = set()
    for src, kinds in (workflow.get("connections") or {}).items():
        for link_kind, outputs in (kinds or {}).items():
            for index, output in enumerate(outputs or []):
                for dst in output or []:
                    out.add((src, f"{link_kind}[{index}]", dst.get("node")))
    return out


def line_diff(before, after) -> list[str]:
    a, b = text(before).splitlines(), text(after).splitlines()
    return [row for row in difflib.unified_diff(a, b, "before", "after", lineterm="", n=1)][2:]


def compare(old: dict, new: dict) -> list[Change]:
    old_nodes = {n.get("name"): n for n in old.get("nodes", [])}
    new_nodes = {n.get("name"): n for n in new.get("nodes", [])}
    gone = sorted(set(old_nodes) - set(new_nodes))
    added = sorted(set(new_nodes) - set(old_nodes))
    renamed = {}
    for name in list(gone):
        twin = [a for a in added if kind(new_nodes[a]) == kind(old_nodes[name])
                and node_settings(new_nodes[a]) == node_settings(old_nodes[name])]
        if len(twin) == 1:
            renamed[name] = twin[0]
            gone.remove(name)
            added.remove(twin[0])
    changes = []
    for name in added:
        changes.append(Change("+node", name, "flow", after=kind(new_nodes[name])))
    for name in gone:
        changes.append(Change("-node", name, "flow", before=kind(old_nodes[name])))
    for old_name, new_name in sorted(renamed.items()):
        changes.append(Change("renamed", new_name, "flow", before=old_name, after=new_name))
    pairs = [(n, n) for n in sorted(set(old_nodes) & set(new_nodes))] + sorted(renamed.items())
    for old_name, new_name in pairs:
        a, b = node_settings(old_nodes[old_name]), node_settings(new_nodes[new_name])
        for key in sorted(set(a) | set(b)):
            if a.get(key) == b.get(key):
                continue
            before, after = a.get(key), b.get(key)
            long = max(len(text(before)), len(text(after))) > LONG or "\n" in text(before) + text(after)
            changes.append(Change("~set", new_name, category(new_nodes[new_name], key), key, before, after,
                                  line_diff(before, after) if long else []))
    rename = {o: n for o, n in renamed.items()}
    old_links = {(rename.get(s, s), k, rename.get(d, d)) for s, k, d in links(old)}
    new_links = links(new)
    for src, link_kind, dst in sorted(new_links - old_links):
        changes.append(Change("+link", src, "flow", link_kind, after=dst))
    for src, link_kind, dst in sorted(old_links - new_links):
        changes.append(Change("-link", src, "flow", link_kind, before=dst))
    return changes


def summary(changes: list[Change]) -> dict:
    counts = {"model": 0, "prompt": 0, "flow": 0}
    for change in changes:
        counts[change.category] += 1
    nodes = {"+": sum(c.op == "+node" for c in changes), "-": sum(c.op == "-node" for c in changes),
             "~": len({c.node for c in changes if c.op == "~set"}), "renamed": sum(c.op == "renamed" for c in changes)}
    return {"total": len(changes), **counts, "nodes": nodes,
            "links": {"+": sum(c.op == "+link" for c in changes), "-": sum(c.op == "-link" for c in changes)}}


def summary_line(s: dict) -> str:
    return f"{s['total']} change(s) · model {s['model']} · prompt {s['prompt']} · flow {s['flow']}"
