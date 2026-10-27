"""Sample company data API for the day 73 labs (day 72 API + employees + ticket contacts; Python standard library only).

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
GET  /admin/fault         -> {"faq": "ok", "tickets": "ok", "slow_seconds": 8}
POST /admin/fault         body {"faq": "ok"|"slow"|"error", "tickets": ..., "slow_seconds": 8}
                          "slow" waits slow_seconds before answering, "error" answers HTTP 500.
GET  /cache/<key>         -> {"key", "value", "hits"} or 404 {"error": "not cached"}
POST /cache/<key>         body {"value": <anything>, "ttl": 600}  (PUT works too)
POST /cache-clear         -> {"cleared": <count>}
GET  /cache-stats         -> {"entries", "hits", "misses"}

Day 73 addition (Lab 03 challenge 2, in memory, newest 1000 kept):
POST /audit               body {"route", "blocked_by", "reason", "masked", ...} -> {"stored": true, "count"}  (security audit log)
GET  /audit               -> {"events": [{"t", ...the body}]}
POST /audit-clear         -> {"cleared": <count>}
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
FAULT = {"faq": "ok", "tickets": "ok", "slow_seconds": 8}
CACHE: dict[str, dict] = {}
STATS = {"hits": 0, "misses": 0}
AUDIT: list[dict] = []


def load(name):
    return json.loads((DATA_DIR / name).read_text(encoding="utf-8"))


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

    def faulty(self, target):
        """Apply the fault switch to one endpoint group. Returns True when the response was already sent."""
        mode = FAULT.get(target, "ok")
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
        return self.send_json(404, {"error": "unknown path"})

    def do_POST(self):
        url = self.url()
        body = self.body()
        if body is None or not isinstance(body, dict):
            return self.send_json(400, {"error": "body must be a JSON object"})
        if url.path == "/admin/fault":
            for target in ("faq", "tickets"):
                if target in body:
                    if body[target] not in ("ok", "slow", "error"):
                        return self.send_json(400, {"error": f"{target} must be ok, slow or error"})
                    FAULT[target] = body[target]
            if "slow_seconds" in body:
                FAULT["slow_seconds"] = max(0.0, min(float(body["slow_seconds"]), 60.0))
            return self.send_json(200, FAULT)
        if url.path == "/audit":
            with LOCK:
                AUDIT.append({"t": round(time.time(), 3), **body})
                del AUDIT[:-1000]
                count = len(AUDIT)
            return self.send_json(200, {"stored": True, "count": count})
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
        return self.send_json(404, {"error": "unknown path"})

    do_PUT = do_POST

    def log_message(self, fmt, *args):
        print(f"{self.address_string()} {fmt % args}", flush=True)


if __name__ == "__main__":
    print(f"data-api listening on :{PORT} (data: {DATA_DIR})", flush=True)
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
