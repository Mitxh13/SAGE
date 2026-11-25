"""
Thin LLM client for the Socratic Tutor.

``generate_json(system, user)`` sends one request and returns the parsed
JSON object.  Provider settings come from the shared backend config
(``LLM_PROVIDER``, ``LLM_MODEL``, ``LLM_API_KEY`` in ``.env``).

Clients
-------
- ``GeminiClient`` — Google Gemini via the ``google-genai`` SDK
- ``FakeLLM``      — scripted responses for offline tests

Any failure (missing config, timeout, API error, unusable JSON) raises
``LLMError`` so the agent can fall back to template replies.

Reference: docs/ARCHITECTURE.md §Stack
"""

from __future__ import annotations

import asyncio
import json
import re
from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel

from backend.config import Settings, get_settings

DEFAULT_TIMEOUT_S = 30.0       # per attempt; comfortable window for local and cloud LLM calls
DEFAULT_TEMPERATURE = 0.4
SUPPORTED_PROVIDERS = ("gemini", "ollama")

_CODE_FENCE = re.compile(r"^```(?:json)?\s*(.*?)\s*```$", re.S)


class LLMError(Exception):
    """The LLM call failed or returned unusable output."""


class LLMConfigError(LLMError):
    """LLM settings in .env are missing or unsupported."""


class BaseLLMClient(ABC):
    """Interface the tutor uses to talk to any LLM provider."""

    @abstractmethod
    async def generate_json(
        self, system: str, user: str, schema: type[BaseModel] | None = None
    ) -> dict[str, Any]:
        """
        Send one request and return the reply as a JSON object.

        :param system: System instructions.
        :param user: The user turn / task prompt.
        :param schema: Optional Pydantic model the reply must follow.
        :raises LLMError: on any failure.
        """


# ════════════════════════════════════════════════════════════════════
# Gemini
# ════════════════════════════════════════════════════════════════════

class GeminiClient(BaseLLMClient):
    """Google Gemini client with JSON output, a timeout and one retry."""

    def __init__(
        self,
        api_key: str,
        model: str,
        timeout_s: float = DEFAULT_TIMEOUT_S,
        temperature: float = DEFAULT_TEMPERATURE,
    ) -> None:
        # Imported here so the backend can import modules.tutor without the SDK.
        from google import genai

        self._client = genai.Client(api_key=api_key)
        self.model = model
        self.timeout_s = timeout_s
        self.temperature = temperature

    async def generate_json(
        self, system: str, user: str, schema: type[BaseModel] | None = None
    ) -> dict[str, Any]:
        import httpx  # installed with google-genai
        from google.genai import errors

        last_error: Exception | None = None
        for _ in range(2):  # one retry on transient failures
            try:
                text = await asyncio.wait_for(self._generate(system, user, schema), self.timeout_s)
                return parse_json_object(text)
            except (TimeoutError, errors.ServerError, httpx.TransportError) as exc:
                last_error = exc
            except errors.APIError as exc:
                raise LLMError(f"Gemini API error {exc.code}: {exc.message}") from exc
        raise LLMError(f"Gemini call failed after one retry: {last_error!r}") from last_error

    async def _generate(self, system: str, user: str, schema: type[BaseModel] | None) -> str:
        from google.genai import types

        response = await self._client.aio.models.generate_content(
            model=self.model,
            contents=user,
            config=types.GenerateContentConfig(
                system_instruction=system,
                temperature=self.temperature,
                response_mime_type="application/json",
                response_schema=schema,
            ),
        )
        if not response.text:
            raise LLMError("Gemini returned an empty response")
        return response.text


# ════════════════════════════════════════════════════════════════════
# Ollama (Local)
# ════════════════════════════════════════════════════════════════════

class OllamaClient(BaseLLMClient):
    """Local Ollama client with JSON mode and connection error handling."""

    def __init__(
        self,
        model: str = "llama3.2:latest",
        base_url: str = "http://localhost:11434",
        timeout_s: float = DEFAULT_TIMEOUT_S,
        temperature: float = DEFAULT_TEMPERATURE,
    ) -> None:
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout_s = timeout_s
        self.temperature = temperature

    async def generate_json(
        self, system: str, user: str, schema: type[BaseModel] | None = None
    ) -> dict[str, Any]:
        import httpx

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "format": "json",
            "stream": False,
            "options": {"temperature": self.temperature},
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout_s) as client:
                resp = await client.post(f"{self.base_url}/api/chat", json=payload)
                if resp.status_code != 200:
                    raise LLMError(f"Ollama returned HTTP {resp.status_code}: {resp.text}")
                data = resp.json()
                raw_text = data.get("message", {}).get("content", "")
                if not raw_text:
                    raise LLMError("Ollama returned an empty response")
                return parse_json_object(raw_text)
        except httpx.ConnectError as exc:
            raise LLMError(
                f"Could not connect to Ollama at {self.base_url}. "
                "Ensure Ollama is running ('ollama serve' or open the Ollama app)."
            ) from exc
        except (httpx.TimeoutException, TimeoutError) as exc:
            raise LLMError(f"Ollama request timed out after {self.timeout_s}s") from exc
        except Exception as exc:
            if isinstance(exc, LLMError):
                raise
            raise LLMError(f"Ollama call failed: {exc}") from exc


# ════════════════════════════════════════════════════════════════════
# Fake (tests)
# ════════════════════════════════════════════════════════════════════

class FakeLLM(BaseLLMClient):
    """Returns scripted responses in order; queued exceptions are raised."""

    def __init__(self, responses: list[dict[str, Any] | Exception]) -> None:
        self._responses = list(responses)
        self.calls: list[tuple[str, str]] = []

    async def generate_json(
        self, system: str, user: str, schema: type[BaseModel] | None = None
    ) -> dict[str, Any]:
        self.calls.append((system, user))
        if not self._responses:
            raise LLMError("FakeLLM has no responses left")
        response = self._responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


# ════════════════════════════════════════════════════════════════════
# Factory & helpers
# ════════════════════════════════════════════════════════════════════

def build_llm_client(settings: Settings | None = None) -> BaseLLMClient:
    """Create the configured LLM client, or raise LLMConfigError."""
    settings = settings or get_settings()
    provider = settings.LLM_PROVIDER.strip().lower()

    if not provider:
        raise LLMConfigError("LLM_PROVIDER is not set in .env")
    if provider not in SUPPORTED_PROVIDERS:
        raise LLMConfigError(
            f"LLM_PROVIDER '{provider}' is not supported by the tutor "
            f"(supported: {', '.join(SUPPORTED_PROVIDERS)})"
        )

    if provider == "ollama":
        model = settings.LLM_MODEL.strip() or "llama3.2:latest"
        return OllamaClient(model=model)

    if not settings.LLM_API_KEY.strip():
        raise LLMConfigError("LLM_API_KEY is not set in .env")
    if not settings.LLM_MODEL.strip():
        raise LLMConfigError("LLM_MODEL is not set in .env")

    return GeminiClient(api_key=settings.LLM_API_KEY.strip(), model=settings.LLM_MODEL.strip())


def parse_json_object(text: str) -> dict[str, Any]:
    """Parse an LLM reply as a JSON object, tolerating a ```json fence."""
    text = text.strip()
    fenced = _CODE_FENCE.match(text)
    if fenced:
        text = fenced.group(1)
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise LLMError(f"LLM reply is not valid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise LLMError(f"LLM reply is JSON but not an object: {type(data).__name__}")
    return data
