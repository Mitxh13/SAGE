"""
Offline tests for the tutor's LLM client.

No test makes a network call: Gemini responses are simulated by
replacing ``GeminiClient._generate``, and ``FakeLLM`` scripts replies.
"""

import asyncio

import pytest
from google.genai import errors

from backend.config import Settings
from modules.tutor import __main__ as cli
from modules.tutor.llm import (
    FakeLLM,
    GeminiClient,
    LLMConfigError,
    LLMError,
    build_llm_client,
    parse_json_object,
)


def _settings(**overrides: str) -> Settings:
    values = {"LLM_PROVIDER": "gemini", "LLM_MODEL": "gemini-test", "LLM_API_KEY": "test-key"}
    values.update(overrides)
    return Settings(_env_file=None, **values)


def _gemini_with(results: list) -> tuple[GeminiClient, list[int]]:
    """GeminiClient whose _generate returns/raises each item of ``results`` in turn."""
    client = GeminiClient(api_key="test-key", model="gemini-test")
    calls: list[int] = []

    async def fake_generate(system, user, schema):
        calls.append(1)
        result = results.pop(0)
        if isinstance(result, Exception):
            raise result
        return result

    client._generate = fake_generate
    return client, calls


def _server_error() -> errors.ServerError:
    return errors.ServerError(503, {"error": {"code": 503, "message": "overloaded", "status": "UNAVAILABLE"}})


def _client_error() -> errors.ClientError:
    return errors.ClientError(400, {"error": {"code": 400, "message": "API key not valid", "status": "INVALID_ARGUMENT"}})


# ════════════════════════════════════════════════════════════════════
# build_llm_client
# ════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"LLM_PROVIDER": ""}, "LLM_PROVIDER is not set"),
        ({"LLM_PROVIDER": "openai"}, "not supported"),
        ({"LLM_API_KEY": ""}, "LLM_API_KEY is not set"),
        ({"LLM_MODEL": "  "}, "LLM_MODEL is not set"),
    ],
)
def test_build_rejects_incomplete_config(overrides: dict, message: str) -> None:
    with pytest.raises(LLMConfigError, match=message):
        build_llm_client(_settings(**overrides))


def test_build_returns_gemini_client() -> None:
    client = build_llm_client(_settings(LLM_PROVIDER=" Gemini "))
    assert isinstance(client, GeminiClient)
    assert client.model == "gemini-test"


# ════════════════════════════════════════════════════════════════════
# GeminiClient retry & error handling
# ════════════════════════════════════════════════════════════════════

def test_gemini_returns_parsed_json() -> None:
    client, calls = _gemini_with(['{"tutor_message": "What did you expect?"}'])
    assert asyncio.run(client.generate_json("sys", "user")) == {"tutor_message": "What did you expect?"}
    assert len(calls) == 1


@pytest.mark.parametrize("transient", [_server_error(), TimeoutError()], ids=["server_error", "timeout"])
def test_gemini_retries_once_on_transient_error(transient: Exception) -> None:
    client, calls = _gemini_with([transient, '{"ok": true}'])
    assert asyncio.run(client.generate_json("sys", "user")) == {"ok": True}
    assert len(calls) == 2


def test_gemini_gives_up_after_one_retry() -> None:
    client, calls = _gemini_with([_server_error(), _server_error()])
    with pytest.raises(LLMError, match="after one retry"):
        asyncio.run(client.generate_json("sys", "user"))
    assert len(calls) == 2


def test_gemini_does_not_retry_client_errors() -> None:
    client, calls = _gemini_with([_client_error()])
    with pytest.raises(LLMError, match="400"):
        asyncio.run(client.generate_json("sys", "user"))
    assert len(calls) == 1


def test_gemini_bad_json_is_an_llm_error() -> None:
    client, _ = _gemini_with(["not json"])
    with pytest.raises(LLMError, match="not valid JSON"):
        asyncio.run(client.generate_json("sys", "user"))


# ════════════════════════════════════════════════════════════════════
# parse_json_object
# ════════════════════════════════════════════════════════════════════

def test_parse_accepts_plain_and_fenced_json() -> None:
    assert parse_json_object('{"a": 1}') == {"a": 1}
    assert parse_json_object('```json\n{"a": 1}\n```') == {"a": 1}


@pytest.mark.parametrize("text", ["", "{broken", "[1, 2]"])
def test_parse_rejects_non_objects(text: str) -> None:
    with pytest.raises(LLMError):
        parse_json_object(text)


# ════════════════════════════════════════════════════════════════════
# FakeLLM & CLI
# ════════════════════════════════════════════════════════════════════

def test_fake_llm_scripts_replies_and_records_calls() -> None:
    fake = FakeLLM([{"n": 1}, LLMError("boom")])
    assert asyncio.run(fake.generate_json("sys", "first")) == {"n": 1}
    with pytest.raises(LLMError, match="boom"):
        asyncio.run(fake.generate_json("sys", "second"))
    with pytest.raises(LLMError, match="no responses left"):
        asyncio.run(fake.generate_json("sys", "third"))
    assert [user for _, user in fake.calls] == ["first", "second", "third"]


def test_cli_check_llm_passes(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setattr(cli, "build_llm_client", lambda: FakeLLM([{"ok": True}]))
    assert cli.main(["--check-llm"]) == 0
    assert "LLM check passed" in capsys.readouterr().out


def test_cli_check_llm_reports_config_error(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def missing_key():
        raise LLMConfigError("LLM_API_KEY is not set in .env")

    monkeypatch.setattr(cli, "build_llm_client", missing_key)
    assert cli.main(["--check-llm"]) == 1
    assert "LLM_API_KEY is not set" in capsys.readouterr().err
