"""Tests for application configuration defaults and overridability."""

import pytest
from app.core.config import Settings

# The committed default must be a model that is currently available via the live
# Gemini API. gemini-2.5-flash was retired for new API users; gemini-3.5-flash-lite
# is the verified replacement default.
DEFAULT_GEMINI_MODEL = "gemini-3.5-flash-lite"


def test_default_gemini_model():
    settings = Settings(_env_file=None)
    assert settings.gemini_model == DEFAULT_GEMINI_MODEL
    # Guard against accidentally restoring the retired default.
    assert settings.gemini_model != "gemini-2.5-flash"


def test_gemini_model_is_overridable_via_init():
    settings = Settings(_env_file=None, gemini_model="gemini-3.8-flash")
    assert settings.gemini_model == "gemini-3.8-flash"


def test_gemini_model_is_env_configurable(monkeypatch):
    monkeypatch.setenv("GEMINI_MODEL", "gemini-flash-latest")
    settings = Settings(_env_file=None)
    assert settings.gemini_model == "gemini-flash-latest"


@pytest.mark.parametrize("provider", ["gemini", "mock"])
def test_llm_provider_is_configurable(provider):
    settings = Settings(_env_file=None, llm_provider=provider)
    assert settings.llm_provider == provider
