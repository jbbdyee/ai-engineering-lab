"""The reading layer (R1 · R4 · R6 · R9 · R10 · R13): the n8n webhooks my-ops-facts · ask · brief · eval and the data API audit.
tops only ever reads: these are the only addresses it calls (R5)."""
from __future__ import annotations

import json
import urllib.error
import urllib.request
from pathlib import Path

READ_ONLY = ("/webhook/my-ops-facts", "/webhook/my-ops-ask", "/webhook/my-ops-brief", "/webhook/my-ops-eval", "/audit/list")


class ReadError(Exception):
    """n8n or the data API did not answer, or a file could not be read (exit code 1)."""


def post(base: str, path: str, body: dict, timeout: float = 60) -> object:
    if path not in READ_ONLY:
        raise ValueError(f"tops does not call {path} (read only)")
    request = urllib.request.Request(base.rstrip("/") + path, data=json.dumps(body).encode(),
                                     headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as answer:
            return json.loads(answer.read())
    except urllib.error.HTTPError as error:
        try:
            return json.loads(error.read())
        except json.JSONDecodeError:
            raise ReadError(f"{base}{path}: HTTP {error.code}") from error
    except (urllib.error.URLError, OSError, json.JSONDecodeError) as error:
        raise ReadError(f"{base}{path}: {error}") from error


def read_json(path: str) -> object:
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ReadError(f"cannot read {path}: {error}") from error


def facts(n8n: str | None = None, file: str | None = None, date_from: str = "", date_to: str = "") -> dict:
    """--file wins over --n8n ($TOPS_N8N may be set for every call)."""
    data = read_json(file) if file else post(n8n or "", "/webhook/my-ops-facts", {"from": date_from, "to": date_to}) if n8n else None
    if data is None:
        raise ReadError("give --n8n (or $TOPS_N8N) or --file")
    if not isinstance(data, dict) or "health" not in data:
        raise ReadError("not the facts of my-ops-facts with health (Lab 01 task 1)")
    return data


def ask(n8n: str, question: str) -> dict:
    return post(n8n, "/webhook/my-ops-ask", {"question": question})


def brief(n8n: str, date_from: str = "", date_to: str = "") -> dict:
    return post(n8n, "/webhook/my-ops-brief", {"from": date_from, "to": date_to})


def evaluate(n8n: str, cases: list, min_score: float | None = None) -> dict:
    body: dict = {"cases": cases}
    if min_score is not None:
        body["min_score"] = min_score
    return post(n8n, "/webhook/my-ops-eval", body, timeout=300)


def audit(api: str) -> dict:
    return post(api, "/audit/list", {})
