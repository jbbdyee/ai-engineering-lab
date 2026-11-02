import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

from tlog import load

DATA = Path(__file__).parent / "data" / "run-logs.json"


@pytest.fixture(scope="session")
def two_weeks():
    """A copy of the course's two weeks of run logs (Last3Mon/77/data-api/data/run-logs.json, 666 runs)."""
    return json.loads(DATA.read_text(encoding="utf-8"))


@pytest.fixture
def api(two_weeks):
    """A local stand-in for the data API: POST /logs/query filters like the real one (dates inclusive)."""
    live = [{"started_at": "2026-11-02T10:00:00", "status": "success", "route": "자동 답변", "duration_ms": 900,
             "topic": "VPN", "tag": "after", "source": "live", "steps": {"faq_ms": 20, "answer_ms": 880}}]

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
            rows = [r for r in two_weeks + live if load.keep(r, body.get("from", ""), body.get("to", ""), body.get("tag", ""),
                                                             body.get("source") or "all")]
            data = json.dumps({"count": len(rows), "logs": rows}, ensure_ascii=False).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(data)

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{server.server_address[1]}"
    server.shutdown()


def run(day, status="success", route="자동 답변", ms=1000, topic="VPN", **extra):
    return {"started_at": day, "status": status, "route": route if status == "success" else None, "duration_ms": ms,
            "topic": topic, "release": "1.0.0", "repeat": False, "steps": {"faq_ms": 20, "answer_ms": ms - 20},
            "cost_usd": 0.0001, "llm_calls": 1, "error_node": None if status == "success" else "Search FAQ",
            "error_message": None if status == "success" else "timeout", **extra}
