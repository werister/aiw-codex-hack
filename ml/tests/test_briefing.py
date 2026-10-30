import asyncio
import copy
import json
from types import SimpleNamespace

import openai
import pytest

from ml import forecast


@pytest.fixture(autouse=True)
def isolated_settings(monkeypatch, tmp_path):
    monkeypatch.setattr(forecast.live, "ROOT", tmp_path)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_MODEL", raising=False)


@pytest.fixture
def result():
    return {"current_od": "25", "next_change": {"from": "25", "to": "07", "p": 0.8,
            "window_local": ["2026-10-31T12:00", "2026-10-31T13:00"]}, "closures_18": [],
            "hours": [{"certainty": 80}, {"certainty": 90}],
            "observed": [{"od": "07", "time": "not-an-input"}]}


def fake_client(monkeypatch, *, text="OD 25 is expected to change. Runway 18 has no inferred weather closure.", error=None, delay=0):
    calls = []

    class Client:
        def __init__(self, **kwargs):
            self.settings = kwargs
            self.responses = self

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        async def create(self, **kwargs):
            calls.append((self.settings, kwargs))
            if delay:
                await asyncio.sleep(delay)
            if error:
                raise error
            return SimpleNamespace(output_text=text)

    monkeypatch.setattr(openai, "AsyncOpenAI", Client)
    return calls


def test_no_key_or_model_skips_request(result, monkeypatch, capsys):
    calls = fake_client(monkeypatch)
    assert forecast.tower_briefing(result) is None
    monkeypatch.setenv("OPENAI_API_KEY", "test-secret")
    assert forecast.tower_briefing(result) is None
    assert calls == []
    assert capsys.readouterr() == ("", "")


def test_success_calls_once_with_given_values_and_leaves_forecast_unchanged(result, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-secret")
    monkeypatch.setenv("OPENAI_MODEL", "configured-model")
    calls = fake_client(monkeypatch)
    before = copy.deepcopy(result)
    assert forecast.tower_briefing(result).startswith("OD 25")
    assert result == before and len(calls) == 1
    settings, request = calls[0]
    assert settings == {"api_key": "test-secret", "timeout": 8.0, "max_retries": 0}
    assert request["model"] == "configured-model" and request["store"] is False
    assert "Use only the given values" in request["instructions"]
    assert "at most 2 sentences" in request["instructions"]
    payload = json.loads(request["input"])
    assert payload["next_change"] == result["next_change"]
    assert payload["certainty_percent_range"] == [80, 90]
    assert "observed" not in payload and "test-secret" not in request["input"]


def test_settings_precedence_and_quoted_file_values(monkeypatch, tmp_path):
    (tmp_path / "web").mkdir()
    (tmp_path / ".env.local").write_text("OPENAI_API_KEY=root-secret\nOPENAI_MODEL=root-model\n")
    (tmp_path / "web/.env.local").write_text('export OPENAI_API_KEY="web-secret" # private\nOPENAI_MODEL=web-model\n')
    assert forecast.briefing_settings() == ("web-secret", "web-model")
    monkeypatch.setenv("OPENAI_API_KEY", "environment-secret")
    monkeypatch.setenv("OPENAI_MODEL", "environment-model")
    assert forecast.briefing_settings() == ("environment-secret", "environment-model")


@pytest.mark.parametrize("error", [RuntimeError("test-secret must not be logged"), TimeoutError("timeout")])
def test_failures_return_null_silently(result, monkeypatch, capsys, error):
    monkeypatch.setenv("OPENAI_API_KEY", "test-secret")
    monkeypatch.setenv("OPENAI_MODEL", "configured-model")
    calls = fake_client(monkeypatch, error=error)
    assert forecast.tower_briefing(result) is None and len(calls) == 1
    assert capsys.readouterr() == ("", "")


def test_eight_second_deadline_cancels_slow_request(result, monkeypatch, capsys):
    monkeypatch.setenv("OPENAI_API_KEY", "test-secret")
    monkeypatch.setenv("OPENAI_MODEL", "configured-model")
    calls = fake_client(monkeypatch, delay=60)
    timeout = asyncio.timeout

    def shortened_timeout(seconds):
        assert seconds == 8
        return timeout(0.01)

    monkeypatch.setattr(forecast.asyncio, "timeout", shortened_timeout)
    assert forecast.tower_briefing(result) is None and len(calls) == 1
    assert capsys.readouterr() == ("", "")


@pytest.mark.parametrize("text", ["Wind will reach 12345 knots.", "First. Second. Third.", "test-secret", ""])
def test_invalid_text_is_discarded(result, monkeypatch, text):
    monkeypatch.setenv("OPENAI_API_KEY", "test-secret")
    monkeypatch.setenv("OPENAI_MODEL", "configured-model")
    fake_client(monkeypatch, text=text)
    assert forecast.tower_briefing(result) is None
