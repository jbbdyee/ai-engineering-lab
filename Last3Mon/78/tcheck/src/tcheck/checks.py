"""The rules, in one place (R13): schema types (R2 · R3), content rules (R8), the gate (R7), the fix list (R9) and
the quality log line (R10). Same codes and the same results as the day 78 n8n my-check (AGENTS.md 3)."""
from __future__ import annotations

import datetime
import math
import re

EMAIL = re.compile(r"^[\w.+-]+@[\w-]+(\.[\w-]+)+$", re.ASCII)
PHONE = re.compile(r"^0\d{1,2}-\d{3,4}-\d{4}$", re.ASCII)
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$", re.ASCII)
PII = (re.compile(r"01[016789][-. ]?\d{3,4}[-. ]?\d{4}", re.ASCII), re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+", re.ASCII))
EXTERNAL = re.compile(r"https?://(?!intra\.example\.com(?![\w.-]))", re.ASCII | re.IGNORECASE)


def js_round(value: float, digits: int = 4) -> float:
    """Half up like JavaScript Math.round (n8n Code nodes), not Python's round-half-even."""
    scale = 10 ** digits
    out = math.floor(value * scale + 0.5) / scale
    return int(out) if out == int(out) else out


def js_str(value) -> str:
    if value is True or value is False:
        return "true" if value else "false"
    if isinstance(value, float) and value == int(value):
        return str(int(value))
    return str(value)


def is_empty(value) -> bool:
    return value is None or (isinstance(value, str) and value.strip() == "") or (isinstance(value, list) and not value)


def is_date(text: str) -> bool:
    if not DATE.match(text):
        return False
    try:
        return datetime.date.fromisoformat(text).isoformat() == text
    except ValueError:
        return False


def field_errors(name: str, rule: dict, value) -> list[str]:
    """One field against one schema rule. The field name never appears in this code (R2)."""
    if is_empty(value):
        return [f"missing:{name}"] if rule.get("required") else []
    kind, text, out = rule.get("type"), js_str(value), []
    if kind == "string":
        if rule.get("max") and len(text) > rule["max"]:
            out.append(f"too_long:{name}")
        if rule.get("min") and len(text) < rule["min"]:
            out.append(f"too_short:{name}")
    elif kind == "enum" and text not in [js_str(v) for v in rule.get("values", [])]:
        out.append(f"not_allowed:{name}")
    elif kind == "email" and not EMAIL.match(text):
        out.append(f"bad_format:{name}")
    elif kind == "phone" and not PHONE.match(text):
        out.append(f"bad_format:{name}")
    elif kind == "date" and not is_date(text):
        out.append(f"bad_format:{name}")
    elif kind == "pattern" and not re.search(rule.get("pattern", ""), text, re.ASCII):
        out.append(f"bad_format:{name}")
    elif kind == "list":
        if not isinstance(value, list):
            out.append(f"bad_format:{name}")
        else:
            if rule.get("min_items") and len(value) < rule["min_items"]:
                out.append(f"too_few:{name}")
            if rule.get("max_items") and len(value) > rule["max_items"]:
                out.append(f"too_many:{name}")
    return out


def content_errors(value) -> list[str]:
    """R8: Lab 01 content rules on a text field (personal phone · e-mail, links outside intra.example.com)."""
    text = "" if value is None else js_str(value).strip()
    out = []
    if any(p.search(text) for p in PII):
        out.append("pii")
    if EXTERNAL.search(text):
        out.append("external_link")
    return out


def check(rows: list, schema: dict, batch: str = "", content: tuple[str, ...] = ()) -> dict:
    """{"schema", "batch", "total", "valid", "invalid", "rows": [{"row", "key", "ok", "errors"}], "codes"} like my-check."""
    seen, out = set(), []
    key_name = schema.get("key", "")
    for index, row in enumerate(rows, 1):
        row = row if isinstance(row, dict) else {}
        errors: list[str] = []
        for name, rule in schema["fields"].items():
            errors += field_errors(name, rule, row.get(name))
        for name in content:
            errors += content_errors(row.get(name))
        key = "" if row.get(key_name) is None else js_str(row.get(key_name))
        if key and key in seen:
            errors.append("duplicate_in_batch")
        if key:
            seen.add(key)
        out.append({"row": index, "key": key, "ok": not errors, "errors": errors})
    codes: dict[str, int] = {}
    for r in out:
        for e in r["errors"]:
            codes[e] = codes.get(e, 0) + 1
    valid = sum(r["ok"] for r in out)
    return {"schema": schema.get("name", ""), "batch": batch, "total": len(out), "valid": valid,
            "invalid": len(out) - valid, "rows": out, "codes": codes}


def score(result: dict) -> float:
    return js_round(result["valid"] / result["total"]) if result["total"] else 0


def gate(result: dict, max_invalid: float = 0.3) -> dict:
    """R7: reject when invalid / total is above the limit (equal passes), like the Lab 02 batch gate."""
    ratio = js_round(result["invalid"] / result["total"]) if result["total"] else 0
    raw = result["invalid"] / result["total"] if result["total"] else 0
    return {"accepted": raw <= max_invalid, "invalid_ratio": ratio, "max_invalid_ratio": max_invalid}


FIX = {
    "missing": "{f} 칸을 채워 주세요",
    "too_long": "{f}을(를) 더 짧게 ({max}자 이내)",
    "too_short": "{f}을(를) 더 길게 ({min}자 이상)",
    "not_allowed": "{f}은(는) {values} 중 하나로",
    "bad_format": "{f}의 형식을 확인해 주세요",
    "too_few": "{f}에 {min_items}개 이상",
    "too_many": "{f}에 {max_items}개 이하",
    "duplicate_in_batch": "같은 배치에 같은 {key}가 또 있습니다. 하나만 남겨 주세요",
    "pii": "개인 전화번호 · 메일 주소를 빼고 IT 포털 안내로 바꿔 주세요",
    "external_link": "바깥 링크 대신 사내 주소(intra.example.com)를 써 주세요",
}


def fix_text(code: str, schema: dict) -> str:
    kind, _, name = code.partition(":")
    rule = schema["fields"].get(name, {})
    values = " · ".join(map(str, rule.get("values", [])))
    return FIX.get(kind, code).format(f=name, key=schema.get("key", "key"), values=values,
                                      max=rule.get("max"), min=rule.get("min"),
                                      min_items=rule.get("min_items"), max_items=rule.get("max_items"))


def fix_list(result: dict, schema: dict) -> dict:
    """R9: what the sender should fix, in row order, plus a one-line message (Lab 01 task 2)."""
    items = [{"row": r["row"], "key": r["key"], "codes": r["errors"], "fix": [fix_text(c, schema) for c in r["errors"]]}
             for r in result["rows"] if r["errors"]]
    message = f"{result['batch']}: {result['total']}줄 중 {result['valid']}줄 통과, {result['invalid']}줄 고칠 것"
    return {"fix_list": items, "message": message}


def quality_entry(result: dict) -> dict:
    """R10: the line my-check writes to /quality-log (Lab 03 task 2)."""
    return {"batch": result["batch"], "dataset": result["schema"], "total": result["total"], "valid": result["valid"],
            "quarantined": result["invalid"], "rejected": False, "score": score(result), "codes": result["codes"]}


def split(rows: list, result: dict) -> tuple[list[dict], list[dict]]:
    """R6: clean rows as they came, rejected rows with an "errors" column."""
    clean = [rows[r["row"] - 1] for r in result["rows"] if r["ok"]]
    rejects = [{**(rows[r["row"] - 1] if isinstance(rows[r["row"] - 1], dict) else {}), "errors": " ".join(r["errors"])}
               for r in result["rows"] if not r["ok"]]
    return clean, rejects
