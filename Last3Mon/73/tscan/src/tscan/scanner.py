"""Find secrets and personal data in text. A finding keeps only the masked value, never the original."""
import re
import unicodedata
from dataclasses import asdict, dataclass

INVISIBLE = re.compile("[​-‍⁠﻿­]")

# (kind, pattern). Boundaries keep dates, versions and long order numbers out.
PATTERNS = [
    ("openai_key", r"(?<![A-Za-z0-9_-])sk-(?:proj-)?[A-Za-z0-9_-]{20,}"),
    ("aws_key", r"(?<![A-Z0-9])AKIA[0-9A-Z]{16}(?![A-Z0-9])"),
    ("github_token", r"(?<![A-Za-z0-9_])gh[pousr]_[A-Za-z0-9]{36,}"),
    ("google_key", r"(?<![A-Za-z0-9_-])AIza[0-9A-Za-z_-]{35}"),
    ("rrn", r"(?<![\d.-])\d{2}(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])-?[1-4]\d{6}(?![\d-])"),
    ("phone", r"(?<![\d.-])01[016789][-. ]?\d{3,4}[-. ]?\d{4}(?![\d-])"),
    ("email", r"(?<![\w.+-])[\w.+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+"),
]
KEY_KINDS = {"openai_key", "aws_key", "github_token", "google_key", "env_value"}


@dataclass(frozen=True)
class Finding:
    kind: str
    path: str
    line: int
    masked: str

    def to_dict(self):
        return asdict(self)


def compile_rules(extra=None):
    """Built-in patterns plus user rules [{"name", "pattern"}] (R11)."""
    rules = [(kind, re.compile(p)) for kind, p in PATTERNS]
    for rule in extra or []:
        rules.append((str(rule["name"]), re.compile(str(rule["pattern"]))))
    return rules


def mask(value, kind):
    if kind == "phone":
        digits = [i for i, ch in enumerate(value) if ch.isdigit()]
        hide = set(digits[3:-4])
        return "".join("*" if i in hide else ch for i, ch in enumerate(value))
    if kind == "email":
        name, _, domain = value.partition("@")
        return f"{name[:1]}***@{domain}"
    if kind == "rrn":
        return value[:6] + "-*******"
    if kind in KEY_KINDS or len(value) >= 8:
        return f"{value[:3]}…****…{value[-2:]}"
    return "*" * len(value)


def clean(line):
    """Same shape for hidden text: full-width to normal (NFKC), invisible characters removed."""
    return INVISIBLE.sub("", unicodedata.normalize("NFKC", line))


def _matches(line, rules, env_values):
    text = clean(line)
    spans = []
    for kind, rule in rules:
        for m in rule.finditer(text):
            spans.append((m.start(), m.end(), kind, m.group(0)))
    for value in env_values:
        start = text.find(value)
        while start != -1:
            spans.append((start, start + len(value), "env_value", value))
            start = text.find(value, start + 1)
    spans.sort(key=lambda s: (s[0], -(s[1] - s[0])))
    chosen, end = [], -1
    for s in spans:  # keep the first, longest match where matches overlap
        if s[0] >= end:
            chosen.append(s)
            end = s[1]
    return text, chosen


def scan_text(text, path="", rules=None, env_values=()):
    rules = rules or compile_rules()
    found = []
    for number, line in enumerate(text.splitlines(), 1):
        _, matches = _matches(line, rules, env_values)
        for _, _, kind, value in matches:
            found.append(Finding(kind, path, number, mask(value, kind)))
    return found


def mask_line(line, rules=None, env_values=()):
    """A whole line with every finding masked (TUI preview, R8)."""
    text, matches = _matches(line, rules or compile_rules(), env_values)
    out, last = [], 0
    for start, end, kind, value in matches:
        out.append(text[last:start])
        out.append(mask(value, kind))
        last = end
    out.append(text[last:])
    return "".join(out)
