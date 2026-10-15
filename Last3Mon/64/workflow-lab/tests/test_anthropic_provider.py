import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

pytest.importorskip("anthropic")

from miniflow import llm  # noqa: E402


class FakeAnthropic(BaseHTTPRequestHandler):
    received: list[dict] = []
    headers_seen: list[dict] = []
    stop_reason = "end_turn"

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        FakeAnthropic.received.append(body)
        FakeAnthropic.headers_seen.append(dict(self.headers))
        reply = {
            "id": "msg_test", "type": "message", "role": "assistant", "model": body["model"],
            "content": [{"type": "text", "text": " network "}],
            "stop_reason": FakeAnthropic.stop_reason, "stop_sequence": None,
            "usage": {"input_tokens": 10, "output_tokens": 2},
        }
        payload = json.dumps(reply).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, *args):
        pass


@pytest.fixture()
def fake_server(monkeypatch):
    server = HTTPServer(("127.0.0.1", 0), FakeAnthropic)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    FakeAnthropic.received.clear()
    FakeAnthropic.headers_seen.clear()
    FakeAnthropic.stop_reason = "end_turn"
    monkeypatch.setenv("MINIFLOW_LLM", "anthropic")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setenv("ANTHROPIC_BASE_URL", f"http://127.0.0.1:{server.server_port}")
    monkeypatch.delenv("ANTHROPIC_MODEL", raising=False)
    yield server
    server.shutdown()


def test_anthropic_request_and_reply(fake_server):
    reply, provider = llm.complete({"temperature": 0}, "문의: VPN", "Reply with the label only.", {})
    assert (reply, provider) == ("network", "anthropic")
    sent = FakeAnthropic.received[-1]
    assert sent["model"] == "claude-opus-5-5"
    assert sent["system"] == "Reply with the label only."
    assert sent["messages"] == [{"role": "user", "content": "문의: VPN"}]
    assert sent["fallbacks"] == "default"
    assert "temperature" not in sent
    assert "server-side-fallback-2026-07-01" in FakeAnthropic.headers_seen[-1].get("anthropic-beta", "")


def test_refusal_is_reported(fake_server):
    FakeAnthropic.stop_reason = "refusal"
    with pytest.raises(llm.LLMError, match="declined"):
        llm.complete({}, "hi", "", {})
