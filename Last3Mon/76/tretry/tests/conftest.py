import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest


class FakeClock:
    """sleep() only moves the clock, so a test never waits and the waits can be checked."""
    def __init__(self):
        self.now = 0.0
        self.slept: list[float] = []

    def sleep(self, seconds: float):
        self.slept.append(seconds)
        self.now += seconds

    def __call__(self):
        return self.now


@pytest.fixture
def clock():
    return FakeClock()


@pytest.fixture
def server():
    """A local server whose answers come from a script: path -> list of (status, body, headers), one per call."""
    script: dict[str, list] = {}
    seen: list[dict] = []

    class Handler(BaseHTTPRequestHandler):
        def answer(self):
            length = int(self.headers.get("Content-Length") or 0)
            seen.append({"path": self.path, "method": self.command, "headers": dict(self.headers),
                         "body": self.rfile.read(length).decode() if length else ""})
            queue = script.get(self.path) or [(200, {"ok": True}, {})]
            status, body, headers = queue.pop(0) if len(queue) > 1 else queue[0]
            if status == "sleep":
                import time
                time.sleep(body)
                status, body, headers = 200, {"late": True}, {}
            data = json.dumps(body).encode()
            self.send_response(status)
            for key, value in headers.items():
                self.send_header(key, value)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        do_GET = do_POST = answer

        def log_message(self, *args):
            pass

    httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{httpd.server_port}", script, seen
    httpd.shutdown()
