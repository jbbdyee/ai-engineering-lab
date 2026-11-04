"""R5 · R13: tops calls only the read addresses; n8n off is a read error, not a crash."""
import pytest

from tops import client


def test_only_read_addresses(fake):
    with pytest.raises(ValueError):
        client.post(fake.base, "/dlq/update", {"id": 1})
    with pytest.raises(ValueError):
        client.post(fake.base, "/ops-reset", {})
    assert fake.calls == []


def test_facts_sends_the_period(fake):
    client.facts(fake.base, date_from="2026-10-19", date_to="2026-10-23")
    assert fake.calls == [("/webhook/my-ops-facts", {"from": "2026-10-19", "to": "2026-10-23"})]


def test_file_wins_over_n8n(fake, tmp_path):
    f = client.facts(fake.base, file=str(__import__("pathlib").Path(__file__).parent / "data" / "facts.json"))
    assert f["overall"] == "red" and fake.calls == []


def test_facts_without_health_is_refused(tmp_path):
    p = tmp_path / "old.json"
    p.write_text('{"runs": {}}')
    with pytest.raises(client.ReadError, match="health"):
        client.facts(file=str(p))


def test_n8n_off_is_read_error(down):
    with pytest.raises(client.ReadError):
        client.ask(down, "지난주 오류율이 얼마야?")


def test_http_error_body_is_returned(fake):
    assert client.evaluate(fake.base, []) == {"error": "cases must be a non-empty list"}
