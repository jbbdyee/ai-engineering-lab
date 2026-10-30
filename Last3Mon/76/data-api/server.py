"""Sample company data API for the day 76 labs (day 75 API + ticket creation + dead letter queue + alerts;
Python standard library only).

GET  /health              -> {"status": "ok"}  (never affected by the fault switch)
GET  /faq?q=<question>    -> {"query": ..., "results": [FAQ entries]}
GET  /tickets/<id>        -> ticket record, or 404 {"error": "ticket not found"}
GET  /tickets/<id>?requester=<name>
                          -> same, but 403 {"error": "not your ticket"} when the ticket belongs to someone else
GET  /employees           -> {"employees": [{"name", "dept"}]}
GET  /employees/<name>    -> {"name", "dept"}, or 404 {"error": "unknown employee"}
GET  /docs                -> {"docs": [{"name", "title"}]}  company IT policy documents (markdown)
GET  /docs/<name>         -> {"name", "title", "text"}, or 404 {"error": "doc not found"}

Day 72 additions (state lives in memory; restarting the container resets it):
GET  /admin/fault         -> {"faq": "ok", "tickets": "ok", "prompts": "ok", "usage": "ok", "dlq": "ok", "slow_seconds": 8}
POST /admin/fault         body {"faq": "ok"|"slow"|"error"|"flaky", "tickets": ..., "prompts": ..., "usage": ..., "dlq": ..., "slow_seconds": 8}
                          "slow" waits slow_seconds before answering, "error" answers HTTP 500,
                          "flaky" fails every second call; for POST /tickets the first try of each key fails
                          and the next one works (a short hiccup).
GET  /cache/<key>         -> {"key", "value", "hits"} or 404 {"error": "not cached"}
POST /cache/<key>         body {"value": <anything>, "ttl": 600}  (PUT works too)
POST /cache-clear         -> {"cleared": <count>}
GET  /cache-stats         -> {"entries", "hits", "misses"}

Day 73 addition (in memory, newest 1000 kept):
POST /audit               body {"route", "blocked_by", "reason", "masked", ...} -> {"stored": true, "count"}
GET  /audit               -> {"events": [{"t", ...the body}]}
POST /audit-clear         -> {"cleared": <count>}

Day 74 additions (prompt registry from data/prompts, releases from data/releases.json, state in memory):
GET  /prompts/<name>         -> {"name", "versions": ["p1", ...]}
GET  /prompts/<name>/<ver>   -> {"name", "version", "text"}, or 404 {"error": "prompt not found"}  (fault switch "prompts")
GET  /releases/<name>        -> {"name", "active", "canary": null | {"release", "percent"}, "require_gate": false, "releases": {...}}
POST /releases/<name>        body {"active": "1.1.0"} and/or {"canary": {"release": "1.2.0", "percent": 50}} or {"canary": null}
                             When require_gate is on, a release can become active or canary only if its latest gate
                             record says "promote"; otherwise 409 {"error": "not gated", "release", "last_gate"}.
POST /releases/<name>/policy body {"require_gate": true|false}
POST /releases/<name>/reset  -> back to data/releases.json (active, no canary, require_gate off; gate records stay)
POST /gates/<name>           body {"release", "verdict": "promote"|"rollback", "passed", "total", "source", ...}
                             -> {"stored": true, "count"}
GET  /gates/<name>           -> {"name", "gates": [{"t", ...the body}]}  (newest last, 200 kept)
POST /gates/<name>/clear     -> {"cleared": <count>}

Day 75 additions (usage and budget in memory):
GET  /prices                 -> {"currency", "unit", "models": {"gpt-4.1-mini": {"input", "output"}, ...}}  (USD per 1M tokens)
POST /usage                  body {"items": [{"request_id", "user", "step", "model", "prompt_tokens",
                             "completion_tokens", "cost_usd", "route"}]} (one item per LLM call, or one item
                             without "items") -> {"stored": n, "total"}  (fault switch "usage": error -> 500,
                             slow -> waits slow_seconds, then 503 and nothing is stored)
GET  /usage/summary          -> {"requests" (distinct request_id), "calls", "prompt_tokens", "completion_tokens",
                             "cost_usd", "by_model", "by_user", "by_route"}  (POST works too)
GET  /usage/user/<name>?window=60 -> {"user", "window", "count"}  distinct requests of that user in the last N seconds
POST /usage-clear            -> {"cleared": n}
GET  /budget                 -> {"daily_usd", "used_usd", "remaining_usd", "over", "user_limit_per_min", "max_question_chars"}
POST /budget                 body {"daily_usd": 0.5} and/or {"user_limit_per_min": 3} and/or {"max_question_chars": 500}
POST /budget/reset           -> back to data/budget.json

Day 76 additions (ticket creation, dead letter queue and alerts in memory):
POST /tickets                body {"key", "title", "requester", "category", "priority"} -> 201 {"ticket_id", "duplicate": false}
                             same "key" again -> 200 {"ticket_id" (the first one), "duplicate": true}  (idempotency)
                             fault switch "tickets": slow waits slow_seconds and then still creates the ticket
                             (a caller that gave up does not know it was made), error -> 500, flaky -> see above
GET  /tickets-created        -> {"count", "tickets": [...]}  (POST /tickets-created/list too);  POST /tickets-reset
POST /dlq                    body {"item", "reason", "workflow"} or {"items": [...]} -> {"stored", "size"}
                             the same item.id again does not add a row: its "attempts" goes up by 1  (fault switch "dlq")
GET  /dlq                    -> {"size", "parked", "items": [{"dlq_id", "item", "reason", "attempts", "parked", ...}]}  (POST /dlq/list too)
POST /dlq/update             body {"dlq_id", "remove": true} or {"dlq_id", "attempts": n, "parked": true, "reason"}
POST /dlq-clear
POST /alerts                 body {"workflow", "node", "message", "severity", "reason", "execution_id", ...} -> {"stored", "count"}
GET  /alerts                 -> {"count", "alerts": [...]}
POST /alerts/list            body {} or filters {"workflow", "reason", "severity", "within": seconds} -> {"count", "alerts"}
POST /alerts/latest          -> the newest alert or {};  POST /alerts-clear
"""

import json
import os
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

DATA_DIR = Path(os.getenv("DATA_DIR", Path(__file__).resolve().parent / "data"))
PORT = int(os.getenv("PORT", "8800"))

LOCK = threading.Lock()
FAULT = {"faq": "ok", "tickets": "ok", "prompts": "ok", "usage": "ok", "dlq": "ok", "slow_seconds": 8}
FLAKY: dict = {}
CACHE: dict[str, dict] = {}
STATS = {"hits": 0, "misses": 0}
AUDIT: list[dict] = []
RELEASES: dict = {}
GATES: dict[str, list[dict]] = {}
USAGE: list[dict] = []
BUDGET: dict = {}
BUDGET_KEYS = {"daily_usd": float, "user_limit_per_min": int, "max_question_chars": int}
CREATED: dict = {}
DLQ: list[dict] = []
ALERTS: list[dict] = []
NEXT = {"ticket": 2001, "dlq": 1}


def dlq_view():
    return {"size": len(DLQ), "parked": sum(1 for e in DLQ if e.get("parked")), "items": DLQ}


def alerts_view(body=None):
    body = body or {}
    now = time.time()
    rows = [a for a in ALERTS
            if all(not body.get(k) or a.get(k) == body[k] for k in ("workflow", "reason", "severity"))
            and (not body.get("within") or now - a["at"] <= float(body["within"]))]
    return {"count": len(rows), "alerts": rows}


def budget():
    if not BUDGET:
        BUDGET.update(load("budget.json"))
    used = round(sum(float(item.get("cost_usd") or 0) for item in USAGE), 8)
    return {**BUDGET, "used_usd": used, "remaining_usd": round(BUDGET["daily_usd"] - used, 8), "over": used >= BUDGET["daily_usd"]}


def summary():
    def add(table, key, item):
        row = table.setdefault(str(key), {"calls": 0, "prompt_tokens": 0, "completion_tokens": 0, "cost_usd": 0.0})
        row["calls"] += 1
        row["prompt_tokens"] += int(item.get("prompt_tokens") or 0)
        row["completion_tokens"] += int(item.get("completion_tokens") or 0)
        row["cost_usd"] = round(row["cost_usd"] + float(item.get("cost_usd") or 0), 8)
    total = {"requests": 0, "calls": 0, "prompt_tokens": 0, "completion_tokens": 0, "cost_usd": 0.0}
    by_model, by_user, by_route = {}, {}, {}
    seen = set()
    for index, item in enumerate(USAGE):
        key = item.get("request_id") or f"item-{index}"
        if key not in seen:
            seen.add(key)
            total["requests"] += 1
        total["calls"] += 1
        total["prompt_tokens"] += int(item.get("prompt_tokens") or 0)
        total["completion_tokens"] += int(item.get("completion_tokens") or 0)
        total["cost_usd"] = round(total["cost_usd"] + float(item.get("cost_usd") or 0), 8)
        add(by_model, item.get("model", "?"), item)
        add(by_user, item.get("user", "?"), item)
        add(by_route, item.get("route", "?"), item)
    return {**total, "by_model": by_model, "by_user": by_user, "by_route": by_route}


def load(name):
    return json.loads((DATA_DIR / name).read_text(encoding="utf-8"))


def releases():
    if not RELEASES:
        for name, item in load("releases.json").items():
            RELEASES[name] = {"active": item["active"], "canary": None, "require_gate": False, "releases": item["releases"]}
    return RELEASES


def last_gate(name, release):
    for record in reversed(GATES.get(name, [])):
        if record.get("release") == release:
            return record
    return None


def search_faq(query, top_k=2):
    words = {word for word in query.lower().split() if len(word) > 1}
    scored = []
    for item in load("faq.json"):
        keywords = {keyword.lower() for keyword in item["keywords"]}
        score = sum(1 for word in words if any(keyword in word or word in keyword for keyword in keywords))
        if score:
            scored.append({"score": score, **item})
    scored.sort(key=lambda item: item["score"], reverse=True)
    return scored[:top_k]


class Handler(BaseHTTPRequestHandler):
    def send_json(self, status, body):
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def url(self):
        # Raw UTF-8 in the request line arrives as latin-1 text; percent-encoded paths are unchanged.
        return urlparse(self.path.encode("latin-1").decode("utf-8", errors="replace"))

    def body(self):
        length = int(self.headers.get("Content-Length") or 0)
        if not length:
            return {}
        try:
            return json.loads(self.rfile.read(length).decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            return None

    def faulty(self, target, key=""):
        """Apply the fault switch to one endpoint group. Returns True when the response was already sent."""
        mode = FAULT.get(target, "ok")
        if mode == "flaky":
            with LOCK:
                slot = f"{target}:{key}" if key else target
                FLAKY[slot] = FLAKY.get(slot, 0) + 1
                fail = FLAKY[slot] == 1 if key else FLAKY[slot] % 2 == 0
            if fail:
                self.send_json(500, {"error": f"{target} service failed this time (flaky fault switch)"})
                return True
            return False
        if mode == "slow":
            time.sleep(float(FAULT.get("slow_seconds", 8)))
        elif mode == "error":
            self.send_json(500, {"error": f"{target} service is failing (fault switch)"})
            return True
        return False

    def do_GET(self):
        url = self.url()
        if url.path == "/health":
            return self.send_json(200, {"status": "ok"})
        if url.path == "/admin/fault":
            return self.send_json(200, FAULT)
        if url.path == "/audit":
            with LOCK:
                return self.send_json(200, {"events": list(AUDIT)})
        if url.path == "/tickets-created":
            with LOCK:
                return self.send_json(200, {"count": len(CREATED), "tickets": list(CREATED.values())})
        if url.path == "/dlq":
            with LOCK:
                return self.send_json(200, dlq_view())
        if url.path == "/alerts":
            with LOCK:
                return self.send_json(200, alerts_view())
        if url.path == "/prices":
            return self.send_json(200, load("prices.json"))
        if url.path == "/usage/summary":
            with LOCK:
                return self.send_json(200, summary())
        if url.path.startswith("/usage/user/"):
            name = unquote(url.path.removeprefix("/usage/user/"))
            window = float(parse_qs(url.query).get("window", ["60"])[0])
            now = time.time()
            with LOCK:
                count = len({item.get("request_id") or f"item-{i}" for i, item in enumerate(USAGE)
                             if item.get("user") == name and now - item["at"] <= window})
            return self.send_json(200, {"user": name, "window": window, "count": count})
        if url.path == "/budget":
            with LOCK:
                return self.send_json(200, budget())
        if url.path == "/cache-stats":
            with LOCK:
                return self.send_json(200, {"entries": len(CACHE), **STATS})
        if url.path.startswith("/cache/"):
            key = unquote(url.path.removeprefix("/cache/"))
            with LOCK:
                entry = CACHE.get(key)
                if entry and entry["expires"] > time.time():
                    entry["hits"] += 1
                    STATS["hits"] += 1
                    return self.send_json(200, {"key": key, "value": entry["value"], "hits": entry["hits"]})
                CACHE.pop(key, None)
                STATS["misses"] += 1
            return self.send_json(404, {"error": "not cached", "key": key})
        if url.path == "/faq":
            if self.faulty("faq"):
                return None
            query = parse_qs(url.query).get("q", [""])[0]
            return self.send_json(200, {"query": query, "results": search_faq(query)})
        if url.path == "/employees":
            return self.send_json(200, {"employees": load("employees.json")})
        if url.path.startswith("/employees/"):
            name = unquote(url.path.removeprefix("/employees/")).strip()
            for person in load("employees.json"):
                if person["name"] == name:
                    return self.send_json(200, person)
            return self.send_json(404, {"error": "unknown employee", "name": name})
        if url.path == "/docs":
            docs = [{"name": f.stem, "title": f.read_text(encoding="utf-8").splitlines()[0].lstrip("# ").strip()}
                    for f in sorted((DATA_DIR / "docs").glob("*.md"))]
            return self.send_json(200, {"docs": docs})
        if url.path.startswith("/docs/"):
            name = unquote(url.path.removeprefix("/docs/")).strip()
            path = DATA_DIR / "docs" / f"{name}.md"
            if "/" in name or not path.exists():
                return self.send_json(404, {"error": "doc not found", "name": name})
            text = path.read_text(encoding="utf-8")
            return self.send_json(200, {"name": name, "title": text.splitlines()[0].lstrip("# ").strip(), "text": text})
        if url.path.startswith("/tickets/"):
            if self.faulty("tickets"):
                return None
            ticket_id = unquote(url.path.removeprefix("/tickets/")).strip().upper()
            ticket = load("tickets.json").get(ticket_id)
            if ticket is None:
                return self.send_json(404, {"error": "ticket not found", "ticket_id": ticket_id})
            requester = parse_qs(url.query).get("requester", [None])[0]
            if requester is not None and requester.strip() != ticket["requester"]:
                return self.send_json(403, {"error": "not your ticket", "ticket_id": ticket_id})
            return self.send_json(200, {"ticket_id": ticket_id, **ticket})
        if url.path.startswith("/prompts/"):
            if self.faulty("prompts"):
                return None
            parts = [unquote(p) for p in url.path.removeprefix("/prompts/").split("/") if p]
            folder = DATA_DIR / "prompts"
            if len(parts) == 1:
                versions = sorted(f.stem.removeprefix(parts[0] + "-") for f in folder.glob(f"{parts[0]}-*.md"))
                return self.send_json(200 if versions else 404, {"name": parts[0], "versions": versions})
            if len(parts) == 2 and "/" not in parts[1] and (folder / f"{parts[0]}-{parts[1]}.md").exists():
                text = (folder / f"{parts[0]}-{parts[1]}.md").read_text(encoding="utf-8").strip()
                return self.send_json(200, {"name": parts[0], "version": parts[1], "text": text})
            return self.send_json(404, {"error": "prompt not found", "path": url.path})
        if url.path.startswith("/releases/"):
            name = unquote(url.path.removeprefix("/releases/")).strip("/")
            with LOCK:
                item = releases().get(name)
                if item is None:
                    return self.send_json(404, {"error": "unknown release name", "name": name})
                return self.send_json(200, {"name": name, **item})
        if url.path.startswith("/gates/"):
            name = unquote(url.path.removeprefix("/gates/")).strip("/")
            with LOCK:
                return self.send_json(200, {"name": name, "gates": list(GATES.get(name, []))})
        return self.send_json(404, {"error": "unknown path"})

    def do_POST(self):
        url = self.url()
        body = self.body()
        if body is None or not isinstance(body, dict):
            return self.send_json(400, {"error": "body must be a JSON object"})
        if url.path == "/admin/fault":
            for target in ("faq", "tickets", "prompts", "usage", "dlq"):
                if target in body:
                    if body[target] not in ("ok", "slow", "error", "flaky"):
                        return self.send_json(400, {"error": f"{target} must be ok, slow, error or flaky"})
                    FAULT[target] = body[target]
                    for slot in [s for s in FLAKY if s == target or s.startswith(target + ":")]:
                        del FLAKY[slot]
            if "slow_seconds" in body:
                FAULT["slow_seconds"] = max(0.0, min(float(body["slow_seconds"]), 60.0))
            return self.send_json(200, FAULT)
        if url.path == "/tickets":
            key = str(body.get("key") or "").strip()
            if self.faulty("tickets", key):
                return None
            if not key or not str(body.get("title") or "").strip():
                return self.send_json(400, {"error": "key and title are required"})
            with LOCK:
                if key in CREATED:
                    return self.send_json(200, {"ticket_id": CREATED[key]["ticket_id"], "duplicate": True})
                ticket_id = f"T-{NEXT['ticket']}"
                NEXT["ticket"] += 1
                CREATED[key] = {"ticket_id": ticket_id, "key": key, **{k: body.get(k) for k in ("title", "requester", "category", "priority")}}
            return self.send_json(201, {"ticket_id": ticket_id, "duplicate": False})
        if url.path == "/tickets-reset":
            with LOCK:
                count = len(CREATED)
                CREATED.clear()
                NEXT["ticket"] = 2001
            return self.send_json(200, {"cleared": count})
        if url.path == "/tickets-created/list":
            with LOCK:
                return self.send_json(200, {"count": len(CREATED), "tickets": list(CREATED.values())})
        if url.path == "/dlq":
            if self.faulty("dlq"):
                return None
            items = body.get("items") if isinstance(body.get("items"), list) else [body]
            with LOCK:
                for item in items:
                    item_id = (item.get("item") or {}).get("id")
                    same = next((e for e in DLQ if item_id and (e.get("item") or {}).get("id") == item_id), None)
                    if same:
                        same["attempts"] += 1
                        same["reason"] = item.get("reason", same.get("reason"))
                        same["at"] = time.time()
                        continue
                    DLQ.append({"dlq_id": f"D-{NEXT['dlq']}", "attempts": 1, "parked": False, **item, "at": time.time()})
                    NEXT["dlq"] += 1
                return self.send_json(200, {"stored": len(items), "size": len(DLQ)})
        if url.path == "/dlq/list":
            with LOCK:
                return self.send_json(200, dlq_view())
        if url.path == "/dlq/update":
            with LOCK:
                for index, entry in enumerate(DLQ):
                    if entry["dlq_id"] == body.get("dlq_id"):
                        if body.get("remove"):
                            DLQ.pop(index)
                            return self.send_json(200, {"removed": True, "size": len(DLQ)})
                        for key in ("attempts", "parked", "reason"):
                            if key in body:
                                entry[key] = body[key]
                        return self.send_json(200, {"updated": True, "entry": entry})
            return self.send_json(404, {"error": "dlq item not found"})
        if url.path == "/dlq-clear":
            with LOCK:
                count = len(DLQ)
                DLQ.clear()
                NEXT["dlq"] = 1
            return self.send_json(200, {"cleared": count})
        if url.path == "/alerts":
            with LOCK:
                ALERTS.append({**body, "at": time.time()})
                return self.send_json(200, {"stored": 1, "count": len(ALERTS)})
        if url.path == "/alerts/list":
            with LOCK:
                return self.send_json(200, alerts_view(body))
        if url.path == "/alerts/latest":
            with LOCK:
                return self.send_json(200, ALERTS[-1] if ALERTS else {})
        if url.path == "/alerts-clear":
            with LOCK:
                count = len(ALERTS)
                ALERTS.clear()
            return self.send_json(200, {"cleared": count})
        if url.path == "/audit":
            with LOCK:
                AUDIT.append({"t": round(time.time(), 3), **body})
                del AUDIT[:-1000]
                count = len(AUDIT)
            return self.send_json(200, {"stored": True, "count": count})
        if url.path == "/usage":
            if FAULT.get("usage") == "slow":
                # a hung record service: answers late and keeps nothing (a caller that gave up must not be counted later)
                time.sleep(float(FAULT.get("slow_seconds", 8)))
                return self.send_json(503, {"error": "usage service timed out (fault switch)", "stored": 0})
            if self.faulty("usage"):
                return None
            items = body.get("items") if isinstance(body.get("items"), list) else [body]
            with LOCK:
                for item in items:
                    USAGE.append({**item, "at": time.time()})
                return self.send_json(200, {"stored": len(items), "total": len(USAGE)})
        if url.path == "/usage/summary":
            with LOCK:
                return self.send_json(200, summary())
        if url.path == "/usage-clear":
            with LOCK:
                count = len(USAGE)
                USAGE.clear()
            return self.send_json(200, {"cleared": count})
        if url.path in ("/budget", "/budget/reset"):
            with LOCK:
                if url.path == "/budget/reset":
                    BUDGET.clear()
                budget()
                for key, kind in BUDGET_KEYS.items():
                    if key in body:
                        BUDGET[key] = kind(body[key])
                return self.send_json(200, budget())
        if url.path == "/audit-clear":
            with LOCK:
                count = len(AUDIT)
                AUDIT.clear()
            return self.send_json(200, {"cleared": count})
        if url.path == "/cache-clear":
            with LOCK:
                count = len(CACHE)
                CACHE.clear()
                STATS.update(hits=0, misses=0)
            return self.send_json(200, {"cleared": count})
        if url.path.startswith("/cache/"):
            key = unquote(url.path.removeprefix("/cache/"))
            if not key or "value" not in body:
                return self.send_json(400, {"error": "key in the path and value in the body are required"})
            ttl = max(1.0, min(float(body.get("ttl", 600)), 86400.0))
            with LOCK:
                CACHE[key] = {"value": body["value"], "expires": time.time() + ttl, "hits": 0}
            return self.send_json(200, {"key": key, "stored": True, "ttl": ttl})
        if url.path.startswith("/gates/"):
            name = unquote(url.path.removeprefix("/gates/")).strip("/")
            clear = name.endswith("/clear")
            name = name.removesuffix("/clear")
            with LOCK:
                if clear:
                    count = len(GATES.pop(name, []))
                    return self.send_json(200, {"cleared": count})
                if not body.get("release") or body.get("verdict") not in ("promote", "rollback"):
                    return self.send_json(400, {"error": "release and verdict (promote or rollback) are required"})
                records = GATES.setdefault(name, [])
                records.append({"t": round(time.time(), 3), **body})
                del records[:-200]
                return self.send_json(200, {"stored": True, "count": len(records)})
        if url.path.startswith("/releases/"):
            name = unquote(url.path.removeprefix("/releases/")).strip("/")
            action = ""
            for suffix in ("/reset", "/policy"):
                if name.endswith(suffix):
                    action, name = suffix[1:], name.removesuffix(suffix)
            with LOCK:
                if action == "reset":
                    RELEASES.pop(name, None)
                item = releases().get(name)
                if item is None:
                    return self.send_json(404, {"error": "unknown release name", "name": name})
                if action == "reset":
                    return self.send_json(200, {"name": name, **item})
                if action == "policy":
                    if not isinstance(body.get("require_gate"), bool):
                        return self.send_json(400, {"error": "require_gate must be true or false"})
                    item["require_gate"] = body["require_gate"]
                    return self.send_json(200, {"name": name, **item})
                wanted = []
                if "active" in body:
                    if body["active"] not in item["releases"]:
                        return self.send_json(400, {"error": "unknown release", "known": sorted(item["releases"])})
                    wanted.append(body["active"])
                canary = body.get("canary")
                if "canary" in body and canary is not None:
                    if not isinstance(canary, dict) or canary.get("release") not in item["releases"] \
                            or not 0 <= int(canary.get("percent", -1)) <= 100:
                        return self.send_json(400, {"error": "canary needs a known release and percent 0..100"})
                    canary = {"release": canary["release"], "percent": int(canary["percent"])}
                    wanted.append(canary["release"])
                if item["require_gate"]:
                    for release in wanted:
                        gate = last_gate(name, release)
                        if not gate or gate.get("verdict") != "promote":
                            return self.send_json(409, {"error": "not gated", "release": release, "last_gate": gate})
                if "active" in body:
                    item["active"] = body["active"]
                if "canary" in body:
                    item["canary"] = canary
                return self.send_json(200, {"name": name, **item})
        return self.send_json(404, {"error": "unknown path"})

    do_PUT = do_POST

    def log_message(self, fmt, *args):
        print(f"{self.address_string()} {fmt % args}", flush=True)


if __name__ == "__main__":
    print(f"data-api listening on :{PORT} (data: {DATA_DIR})", flush=True)
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
