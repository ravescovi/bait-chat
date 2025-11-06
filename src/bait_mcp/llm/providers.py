"""Helpers for working with different LLM providers."""

from __future__ import annotations

import os
from abc import ABC, abstractmethod
from typing import Dict, List, Optional

import aiohttp

Message = Dict[str, str]


class LLMProviderError(RuntimeError):
    """Raised when an LLM provider cannot fulfil a request."""


class LLMProvider(ABC):
    """Abstract base class for chat completion providers."""

    def __init__(self) -> None:
        self._identifier: Optional[str] = None

    @property
    def identifier(self) -> Optional[str]:
        """String describing the model/endpoint backing this provider."""

        return self._identifier

    @abstractmethod
    async def chat(
        self,
        messages: List[Message],
        *,
        temperature: float = 0.7,
        max_tokens: int = 500,
    ) -> str:
        """Return the assistant content for the supplied message list."""


def _normalise_base_url(base_url: str) -> str:
    cleaned = base_url.rstrip("/")
    if not cleaned.endswith("/v1"):
        cleaned = f"{cleaned}/v1"
    return cleaned


class LMStudioProvider(LLMProvider):
    """Provider that talks to an LMStudio OpenAI-compatible endpoint."""

    def __init__(self, model_url: Optional[str] = None, timeout: float = 30.0) -> None:
        super().__init__()
        base_url = model_url or os.environ.get("LMSTUDIO_BASE_URL")
        if base_url:
            cleaned = base_url.rstrip("/")
        else:
            fallback = os.environ.get("LMSTUDIO_URL", "http://127.0.0.1:1234")
            cleaned = fallback.rstrip("/")
        cleaned = _normalise_base_url(cleaned)
        self._endpoint = f"{cleaned}/chat/completions"
        self._timeout = timeout
        self._identifier = self._endpoint

    async def chat(
        self,
        messages: List[Message],
        *,
        temperature: float = 0.7,
        max_tokens: int = 500,
    ) -> str:
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer lm-studio",
        }
        payload = {
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        connector = aiohttp.TCPConnector(ssl=False)
        timeout = aiohttp.ClientTimeout(total=self._timeout)
        try:
            async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
                async with session.post(self._endpoint, json=payload, headers=headers) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise LLMProviderError(
                            f"LMStudio request failed with status {response.status}: {error_text}"
                        )
                    result = await response.json()
        except aiohttp.ClientConnectorError as exc:
            raise LLMProviderError(
                "LMStudio is not running. Please start LMStudio and ensure the OpenAI-compatible server is available."
            ) from exc
        try:
            return result["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:  # pragma: no cover - defensive
            raise LLMProviderError("Unexpected LMStudio response format") from exc


class OpenAIProvider(LLMProvider):
    """Provider that uses the official OpenAI Python SDK."""

    def __init__(
        self,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: float = 30.0,
    ) -> None:
        super().__init__()
        from openai import AsyncOpenAI

        resolved_model = (
            model or os.environ.get("OPENAI_MODEL") or os.environ.get("LLM_MODEL") or "gpt-4o-mini"
        )
        resolved_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not resolved_key:
            raise LLMProviderError("OPENAI_API_KEY must be set to use the OpenAI provider.")

        resolved_base = (
            base_url or os.environ.get("OPENAI_BASE_URL") or os.environ.get("OPENAI_API_BASE")
        )
        client_kwargs = {"api_key": resolved_key, "timeout": timeout}
        if resolved_base:
            client_kwargs["base_url"] = resolved_base
        organization = os.environ.get("OPENAI_ORG_ID") or os.environ.get("OPENAI_ORGANIZATION")
        if organization:
            client_kwargs["organization"] = organization

        self._client = AsyncOpenAI(**client_kwargs)
        self._model = resolved_model
        self._identifier = f"openai:{resolved_model}"

    async def chat(
        self,
        messages: List[Message],
        *,
        temperature: float = 0.7,
        max_tokens: int = 500,
    ) -> str:
        response = await self._client.chat.completions.create(
            model=self._model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        content = response.choices[0].message.content
        return content or ""


class AgentKitProvider(LLMProvider):
    """Provider that delegates to AgentKit's litellm wrapper."""

    def __init__(
        self,
        model: Optional[str] = None,
        api_base: Optional[str] = None,
        api_key: Optional[str] = None,
    ) -> None:
        super().__init__()
        from agentkit.processor import llm_chat

        self._llm_chat = llm_chat
        self._model = (
            model
            or os.environ.get("AGENTKIT_MODEL")
            or os.environ.get("OPENAI_MODEL")
            or os.environ.get("LLM_MODEL")
            or "gpt-4o-mini"
        )
        self._api_base = (
            api_base
            or os.environ.get("AGENTKIT_API_BASE")
            or os.environ.get("OPENAI_API_BASE")
            or os.environ.get("OPENAI_BASE_URL")
        )
        self._api_key = (
            api_key or os.environ.get("AGENTKIT_API_KEY") or os.environ.get("OPENAI_API_KEY")
        )
        self._identifier = f"agentkit:{self._model}"

    async def chat(
        self,
        messages: List[Message],
        *,
        temperature: float = 0.7,
        max_tokens: int = 500,
    ) -> str:
        # AgentKit's helper does not currently expose temperature/max_tokens controls.
        try:
            return await self._llm_chat(
                self._model,
                messages,
                api_base=self._api_base,
                api_key=self._api_key,
            )
        except Exception as exc:  # pragma: no cover - depends on external backend
            raise LLMProviderError(f"AgentKit request failed: {exc}") from exc


class OpenAICompatibleProvider(LLMProvider):
    """Fallback provider for generic OpenAI-compatible HTTP endpoints."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        provider_name: Optional[str] = None,
        timeout: float = 30.0,
    ) -> None:
        super().__init__()
        resolved_base = base_url
        if not resolved_base and provider_name == "ollama":
            resolved_base = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
        if not resolved_base:
            resolved_base = (
                os.environ.get("CUSTOM_LLM_URL")
                or os.environ.get("LLM_API_BASE")
                or os.environ.get("OPENAI_BASE_URL")
            )
        if not resolved_base:
            raise LLMProviderError(
                "A model_url or CUSTOM_LLM_URL environment variable is required for OpenAI-compatible providers."
            )
        cleaned = _normalise_base_url(resolved_base)
        self._endpoint = f"{cleaned}/chat/completions"
        self._model = (
            model
            or os.environ.get("CUSTOM_LLM_MODEL")
            or os.environ.get("LLM_MODEL")
            or "gpt-3.5-turbo"
        )
        self._api_key = (
            api_key or os.environ.get("CUSTOM_LLM_API_KEY") or os.environ.get("LLM_API_KEY")
        )
        self._timeout = timeout
        self._identifier = self._endpoint

    async def chat(
        self,
        messages: List[Message],
        *,
        temperature: float = 0.7,
        max_tokens: int = 500,
    ) -> str:
        headers = {"Content-Type": "application/json"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"
        payload = {
            "model": self._model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        timeout = aiohttp.ClientTimeout(total=self._timeout)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(self._endpoint, json=payload, headers=headers) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise LLMProviderError(
                        f"OpenAI-compatible request failed with status {response.status}: {error_text}"
                    )
                result = await response.json()
        try:
            return result["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:  # pragma: no cover - defensive
            raise LLMProviderError("Unexpected OpenAI-compatible response format") from exc


def create_llm_provider(provider_name: str, model_url: Optional[str] = None) -> LLMProvider:
    """Create a provider instance from configuration."""

    normalised = (provider_name or "lmstudio").lower()
    try:
        if normalised == "lmstudio":
            return LMStudioProvider(model_url=model_url)
        if normalised == "openai":
            return OpenAIProvider(base_url=model_url)
        if normalised == "agentkit":
            return AgentKitProvider(api_base=model_url)
        return OpenAICompatibleProvider(base_url=model_url, provider_name=normalised)
    except ImportError as exc:  # pragma: no cover - depends on optional deps
        missing = "openai" if normalised == "openai" else "agentkit"
        raise LLMProviderError(
            f"The '{normalised}' provider requires the `{missing}` package. Install it to use this provider."
        ) from exc
