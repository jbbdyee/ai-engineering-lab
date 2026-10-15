import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from miniflow import llm


class FakeOllama(BaseHTTPRequestHandler):
    received: list[dict] = []

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        FakeOllama.received.append(body)
        if body["model"] == "missing-model":
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'{"error":"model not found"}')
            return
        reply = {"message": {"role": "assistant", "content": " network \n"}, "done": True}
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
    server = HTTPServer(("127.0.0.1", 0), FakeOllama)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    FakeOllama.received.clear()
    monkeypatch.setenv("MINIFLOW_LLM", "ollama")
    monkeypatch.setenv("OLLAMA_HOST", f"127.0.0.1:{server.server_port}")
    monkeypatch.setenv("OLLAMA_MODEL", "gemma3:1b")
    yield server
    server.shutdown()


def test_ollama_request_and_reply(fake_server):
    reply, provider = llm.complete({"temperature": 0}, "문의: VPN", "Reply with the label only.", {})
    assert (reply, provider) == ("network", "ollama")
    sent = FakeOllama.received[-1]
    assert sent["model"] == "gemma3:1b"
    assert sent["stream"] is False
    assert sent["messages"][0] == {"role": "system", "content": "Reply with the label only."}
    assert sent["messages"][1]["content"] == "문의: VPN"


def test_missing_model_gives_pull_hint(fake_server, monkeypatch):
    monkeypatch.setenv("OLLAMA_MODEL", "missing-model")
    with pytest.raises(llm.LLMError, match="ollama pull missing-model"):
        llm.complete({}, "hi", "", {})


def test_unreachable_server(monkeypatch):
    monkeypatch.setenv("MINIFLOW_LLM", "ollama")
    monkeypatch.setenv("OLLAMA_HOST", "http://127.0.0.1:9")
    monkeypatch.setenv("OLLAMA_TIMEOUT", "2")
    with pytest.raises(llm.LLMError, match="Cannot reach Ollama"):
        llm.complete({}, "hi", "", {})
