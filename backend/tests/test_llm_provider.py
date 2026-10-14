"""Tests for the Gemini provider error normalisation (no real network calls)."""

import pytest
from app.services.llm_provider import (
    GeminiProvider,
    LLMConfigError,
    LLMQuotaError,
    LLMTimeoutError,
    LLMUpstreamError,
)


def test_missing_api_key_raises_config_error():
    with pytest.raises(LLMConfigError):
        GeminiProvider(api_key="", model="gemini-2.5-flash")


class _FakeExc(Exception):
    def __init__(self, msg, code=None):
        super().__init__(msg)
        self.code = code


def _provider_with_stub(monkeypatch, raised=None, text="ok"):
    """Build a GeminiProvider whose underlying client is a stub."""
    # Avoid importing the real SDK client: patch after construction.

    class _Models:
        def generate_content(self, **kwargs):
            if raised is not None:
                raise raised
            return type("R", (), {"text": text})()

    class _Client:
        models = _Models()

    # Build without the real SDK by monkeypatching genai.Client via the module.
    provider = GeminiProvider.__new__(GeminiProvider)
    provider.model_name = "gemini-2.5-flash"
    provider._temperature = 0.2
    provider._max_output_tokens = 256
    provider._timeout_ms = 30000

    class _Types:
        def GenerateContentConfig(self, **kwargs):
            return kwargs

    provider._types = _Types()
    provider._client = _Client()
    return provider


def test_timeout_is_mapped(monkeypatch):
    p = _provider_with_stub(monkeypatch, raised=_FakeExc("deadline exceeded"))
    with pytest.raises(LLMTimeoutError):
        p.generate(system_instruction="s", prompt="p")


def test_quota_is_mapped(monkeypatch):
    p = _provider_with_stub(monkeypatch, raised=_FakeExc("quota exceeded", code=429))
    with pytest.raises(LLMQuotaError):
        p.generate(system_instruction="s", prompt="p")


def test_auth_is_mapped(monkeypatch):
    p = _provider_with_stub(monkeypatch, raised=_FakeExc("permission denied", code=403))
    with pytest.raises(LLMConfigError):
        p.generate(system_instruction="s", prompt="p")


def test_empty_response_is_upstream_error(monkeypatch):
    p = _provider_with_stub(monkeypatch, text="")
    with pytest.raises(LLMUpstreamError):
        p.generate(system_instruction="s", prompt="p")


def test_successful_generation_returns_text(monkeypatch):
    p = _provider_with_stub(monkeypatch, text="hello there")
    assert p.generate(system_instruction="s", prompt="p") == "hello there"
