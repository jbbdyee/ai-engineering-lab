"""Sample company data API for the day 71 labs (day 67 API + policy documents; Python standard library only).

GET /health              -> {"status": "ok"}
GET /faq?q=<question>    -> {"query": ..., "results": [FAQ entries]}
GET /tickets/<id>        -> ticket record, or 404 {"error": "ticket not found"}
GET /tickets/<id>?requester=<name>
                         -> same, but 403 {"error": "not your ticket"} when the ticket belongs to someone else
GET /docs                -> {"docs": [{"name", "title"}]}  company IT policy documents (markdown)
GET /docs/<name>         -> {"name", "title", "text"}, or 404 {"error": "doc not found"}
"""

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

DATA_DIR = Path(os.getenv("DATA_DIR", Path(__file__).resolve().parent / "data"))
PORT = int(os.getenv("PORT", "8800"))


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

    def do_GET(self):
        # Raw UTF-8 in the request line arrives as latin-1 text; percent-encoded paths are unchanged.
        url = urlparse(self.path.encode("latin-1").decode("utf-8", errors="replace"))
        if url.path == "/health":
            return self.send_json(200, {"status": "ok"})
        if url.path == "/faq":
            query = parse_qs(url.query).get("q", [""])[0]
            return self.send_json(200, {"query": query, "results": search_faq(query)})
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
            ticket_id = unquote(url.path.removeprefix("/tickets/")).strip().upper()
            ticket = load("tickets.json").get(ticket_id)
            if ticket is None:
                return self.send_json(404, {"error": "ticket not found", "ticket_id": ticket_id})
            requester = parse_qs(url.query).get("requester", [None])[0]
            if requester is not None and requester.strip() != ticket["requester"]:
                return self.send_json(403, {"error": "not your ticket", "ticket_id": ticket_id})
            return self.send_json(200, {"ticket_id": ticket_id, **ticket})
        return self.send_json(404, {"error": "unknown path"})

    def log_message(self, fmt, *args):
        print(f"{self.address_string()} {fmt % args}", flush=True)


if __name__ == "__main__":
    print(f"data-api listening on :{PORT} (data: {DATA_DIR})", flush=True)
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
