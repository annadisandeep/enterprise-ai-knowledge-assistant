"""LLM provider abstraction.

A thin interface over the answer-generation model so the RAG engine is decoupled
from any single vendor and so tests can inject a deterministic mock. The real
implementation uses Google's official ``google-genai`` SDK. All provider failures
are normalised into :class:`LLMError` subclasses carrying *safe* messages (never
raw provider internals or keys).
"""

from __future__ import annotations

import logging
from typing import Protocol, runtime_checkable

logger = logging.getLogger(__name__)


class LLMError(Exception):
    """Base class for provider failures. ``str(self)`` is safe to show users."""


class LLMConfigError(LLMError):
    """Missing/invalid credentials or configuration."""


class LLMTimeoutError(LLMError):
    """The provider did not respond in time."""


class LLMQuotaError(LLMError):
    """Rate limit / quota exceeded."""


class LLMUpstreamError(LLMError):
    """Provider returned an error or an empty/blocked response."""


@runtime_checkable
class LLMProvider(Protocol):
    model_name: str

    def generate(self, *, system_instruction: str, prompt: str) -> str: ...


class GeminiProvider:
    """Answer generation via Google Gemini (``google-genai`` SDK)."""

    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        temperature: float = 0.2,
        max_output_tokens: int = 1024,
        timeout_seconds: float = 30.0,
    ) -> None:
        if not api_key:
            raise LLMConfigError("The AI service is not configured (missing API key).")
        self.model_name = model
        self._temperature = temperature
        self._max_output_tokens = max_output_tokens
        self._timeout_ms = int(timeout_seconds * 1000)
        try:
            from google import genai
            from google.genai import types

            self._types = types
            self._client = genai.Client(
                api_key=api_key,
                http_options=types.HttpOptions(timeout=self._timeout_ms),
            )
        except LLMError:
            raise
        except Exception as exc:  # noqa: BLE001 - SDK import/init failures
            raise LLMConfigError("Failed to initialise the AI client.") from exc

    def generate(self, *, system_instruction: str, prompt: str) -> str:
        types = self._types
        try:
            response = self._client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=self._temperature,
                    max_output_tokens=self._max_output_tokens,
                ),
            )
        except Exception as exc:  # noqa: BLE001 - normalise all SDK errors
            raise self._map_error(exc) from exc

        text = getattr(response, "text", None)
        if not text or not text.strip():
            raise LLMUpstreamError("The AI service returned an empty response.")
        return text.strip()

    def _map_error(self, exc: Exception) -> LLMError:
        name = type(exc).__name__.lower()
        message = str(exc).lower()
        status_code = getattr(exc, "code", None) or getattr(exc, "status_code", None)
        if "timeout" in name or "timeout" in message or "deadline" in message:
            logger.warning("Gemini timeout: %s", exc)
            return LLMTimeoutError("The AI service timed out. Please try again.")
        if status_code in (401, 403) or "permission" in message or "api key" in message:
            logger.error("Gemini auth error: %s", exc)
            return LLMConfigError("The AI service rejected the credentials.")
        if status_code == 429 or "quota" in message or "rate limit" in message:
            logger.warning("Gemini quota error: %s", exc)
            return LLMQuotaError("The AI service is rate-limited. Please try again shortly.")
        logger.error("Gemini upstream error: %s", exc)
        return LLMUpstreamError("The AI service is temporarily unavailable.")


class MockLLMProvider:
    """Deterministic provider for tests and offline/local use.

    By default it returns a short answer that quotes the start of the supplied
    context, so the RAG pipeline can be exercised end to end without any network
    call. Tests can override ``response``, supply a ``handler`` callable, or set
    ``error`` to simulate provider failures.
    """

    def __init__(
        self,
        *,
        model: str = "mock-model",
        response: str | None = None,
        handler=None,
        error: Exception | None = None,
    ) -> None:
        self.model_name = model
        self.response = response
        self.handler = handler
        self.error = error
        self.last_system_instruction: str | None = None
        self.last_prompt: str | None = None

    def generate(self, *, system_instruction: str, prompt: str) -> str:
        self.last_system_instruction = system_instruction
        self.last_prompt = prompt
        if self.error is not None:
            raise self.error
        if self.handler is not None:
            return self.handler(system_instruction, prompt)
        if self.response is not None:
            return self.response
        return "Based on the provided documents, here is a grounded answer. [Source 1]"
