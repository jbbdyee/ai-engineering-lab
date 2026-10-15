"""OpenAI provider, .env loading and the Ollama fallback, without network access."""

import types

import pytest

from miniflow import envfile, llm


def test_parse_env_lines():
    values = envfile.parse('# comment\nexport A=1\nB="two words"\nC=3  # note\n\nbroken line\n')
    assert values == {"A": "1", "B": "two words", "C": "3"}


def test_load_keeps_shell_values(tmp_path, monkeypatch):
    (tmp_path / ".env").write_text("MINIFLOW_TEST_A=from-file\nMINIFLOW_TEST_B=from-file\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("MINIFLOW_DOTENV", "1")
    monkeypatch.setenv("MINIFLOW_TEST_A", "from-shell")
    monkeypatch.delenv("MINIFLOW_TEST_B", raising=False)
    assert envfile.load() == tmp_path / ".env"
    assert llm.os.environ["MINIFLOW_TEST_A"] == "from-shell"
    assert llm.os.environ["MINIFLOW_TEST_B"] == "from-file"
    monkeypatch.delenv("MINIFLOW_TEST_B")


def test_openai_without_key(monkeypatch):
    monkeypatch.setenv("MINIFLOW_LLM", "openai")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("MINIFLOW_LLM_FALLBACK", raising=False)
    with pytest.raises(llm.LLMError, match="OPENAI_API_KEY"):
        llm.complete({}, "hello", "", {})


def test_openai_request_shape(monkeypatch):
    sent = {}

    class FakeResponses:
        def create(self, **kwargs):
            sent.update(kwargs)
            return types.SimpleNamespace(output_text='{"ok": true}', usage=None)

    class FakeClient:
        def __init__(self, **_):
            self.responses = FakeResponses()

    import openai

    monkeypatch.setattr(openai, "OpenAI", FakeClient)
    monkeypatch.setenv("MINIFLOW_LLM", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("OPENAI_MODEL", "test-model")
    schema = {"type": "object", "properties": {"ok": {"type": "boolean"}}}
    reply, used = llm.complete({"temperature": 0, "json_schema": schema}, "hello", "be brief", {})
    assert (reply, used) == ('{"ok": true}', "openai")
    assert sent["model"] == "test-model" and sent["instructions"] == "be brief" and sent["temperature"] == 0
    assert sent["text"]["format"]["schema"] == schema


def test_fallback_to_second_provider(monkeypatch, capsys):
    monkeypatch.setenv("MINIFLOW_LLM", "openai")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("MINIFLOW_LLM_FALLBACK", "ollama")
    monkeypatch.setattr(llm, "call_ollama", lambda *args, **kwargs: "from ollama")
    reply, used = llm.complete({}, "hello", "", {})
    assert (reply, used) == ("from ollama", "ollama")
    assert "openai failed" in capsys.readouterr().err


def test_both_providers_fail(monkeypatch):
    monkeypatch.setenv("MINIFLOW_LLM", "openai")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("MINIFLOW_LLM_FALLBACK", "ollama")

    def broken(*args, **kwargs):
        raise llm.LLMError("Cannot reach Ollama")

    monkeypatch.setattr(llm, "call_ollama", broken)
    with pytest.raises(llm.LLMError, match="OPENAI_API_KEY.*fallback ollama failed"):
        llm.complete({}, "hello", "", {})
