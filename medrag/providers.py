from __future__ import annotations

import json
import os
import urllib.parse
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

import httpx


class ProviderError(RuntimeError):
    def __init__(self, message: str, status_code: int | None = None, retry_after: float | None = None):
        super().__init__(message)
        self.status_code = status_code
        self.retry_after = retry_after


class LLMProvider(ABC):
    name = "unknown"
    model = "unknown"

    @abstractmethod
    def generate(self, prompt: str, system: str = "", temperature: float = 0.1) -> str:
        raise NotImplementedError

    def generate_json(self, prompt: str, system: str = "", temperature: float = 0.0) -> Any:
        return parse_json_response(self.generate(prompt, system, temperature))


def _request_json(url: str, payload: dict[str, Any], headers: dict[str, str], timeout: int = 180) -> dict[str, Any]:
    request_headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": "MedVale-RAG-Lab/0.1",
        **headers,
    }
    try:
        with httpx.Client(timeout=timeout, follow_redirects=False) as client:
            response = client.post(url, json=payload, headers=request_headers)
        if response.is_error:
            detail = response.text[:2000]
            try:
                retry_after = float(response.headers.get("retry-after", ""))
            except ValueError:
                retry_after = None
            if response.status_code in {401, 403}:
                raise ProviderError(
                    f"provider HTTP {response.status_code}: access was rejected. "
                    "Check the API key, base URL, and whether a proxy/VPN is filtering the request. "
                    f"Provider response: {detail}", response.status_code, retry_after
                )
            raise ProviderError(f"provider HTTP {response.status_code}: {detail}", response.status_code, retry_after)
        try:
            return response.json()
        except ValueError as exc:
            raise ProviderError(f"provider returned non-JSON content: {response.text[:1000]}") from exc
    except httpx.RequestError as exc:
        raise ProviderError(f"provider connection failed: {exc}") from exc


def parse_json_response(text: str) -> Any:
    cleaned = (text or "").strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
    for left, right in (("[", "]"), ("{", "}")):
        start, end = cleaned.find(left), cleaned.rfind(right)
        if start >= 0 and end > start:
            try:
                return json.loads(cleaned[start : end + 1])
            except json.JSONDecodeError:
                pass
    raise ProviderError("model did not return valid JSON")


@dataclass
class OllamaProvider(LLMProvider):
    base_url: str
    model: str
    name: str = "ollama"

    def generate(self, prompt: str, system: str = "", temperature: float = 0.1) -> str:
        data = _request_json(
            f"{self.base_url.rstrip('/')}/api/generate",
            {"model": self.model, "prompt": prompt, "system": system, "stream": False, "options": {"temperature": temperature}},
            {},
        )
        return str(data.get("response", "")).strip()


@dataclass
class OpenAICompatibleProvider(LLMProvider):
    base_url: str
    api_key: str
    model: str
    name: str = "openai_compatible"

    def generate(self, prompt: str, system: str = "", temperature: float = 0.1) -> str:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        data = _request_json(
            f"{self.base_url.rstrip('/')}/chat/completions",
            {"model": self.model, "messages": messages, "temperature": temperature},
            {"Authorization": f"Bearer {self.api_key}"},
        )
        try:
            return str(data["choices"][0]["message"]["content"]).strip()
        except (KeyError, IndexError, TypeError) as exc:
            raise ProviderError(f"unexpected compatible API response: {data}") from exc


@dataclass
class OpenAIResponsesProvider(LLMProvider):
    api_key: str
    model: str
    base_url: str = "https://api.openai.com/v1"
    name: str = "openai"

    def generate(self, prompt: str, system: str = "", temperature: float = 0.1) -> str:
        payload: dict[str, Any] = {"model": self.model, "input": prompt, "store": False}
        if system:
            payload["instructions"] = system
        data = _request_json(
            f"{self.base_url.rstrip('/')}/responses",
            payload,
            {"Authorization": f"Bearer {self.api_key}"},
        )
        if data.get("output_text"):
            return str(data["output_text"]).strip()
        texts = []
        for item in data.get("output", []):
            for content in item.get("content", []):
                if content.get("type") == "output_text":
                    texts.append(content.get("text", ""))
        if texts:
            return "\n".join(texts).strip()
        raise ProviderError(f"unexpected OpenAI Responses payload: {data}")


@dataclass
class GeminiProvider(LLMProvider):
    api_key: str
    model: str
    name: str = "gemini"

    def generate(self, prompt: str, system: str = "", temperature: float = 0.1) -> str:
        url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"{urllib.parse.quote(self.model, safe='')}:generateContent?key={urllib.parse.quote(self.api_key)}"
        )
        full_prompt = f"SYSTEM:\n{system}\n\n{prompt}" if system else prompt
        data = _request_json(
            url,
            {"contents": [{"parts": [{"text": full_prompt}]}], "generationConfig": {"temperature": temperature}},
            {},
        )
        try:
            return "".join(p.get("text", "") for p in data["candidates"][0]["content"]["parts"]).strip()
        except (KeyError, IndexError, TypeError) as exc:
            raise ProviderError(f"unexpected Gemini response: {data}") from exc


class MockProvider(LLMProvider):
    name = "mock"
    model = "deterministic-mock"

    def generate(self, prompt: str, system: str = "", temperature: float = 0.1) -> str:
        if '"nodes"' in prompt and '"edges"' in prompt:
            return '{"nodes": [], "edges": []}'
        if '"stem"' in prompt and '"choices"' in prompt:
            return json.dumps({
                "stem": "A patient presents with a deterministic clinical vignette used only for integration testing. The history, examination, and diagnostic studies provide several converging clues without relying on a single giveaway phrase.",
                "lead_in": "Which of the following is the most appropriate interpretation?",
                "choices": [
                    {"id": "A", "text": "Correct interpretation", "explanation": "This best fits the supplied evidence."},
                    {"id": "B", "text": "First distractor", "explanation": "This conflicts with a key finding."},
                    {"id": "C", "text": "Second distractor", "explanation": "This would require a missing feature."},
                    {"id": "D", "text": "Third distractor", "explanation": "This does not explain the presentation."},
                    {"id": "E", "text": "Fourth distractor", "explanation": "This is less appropriate than the keyed answer."},
                ],
                "correct_choice_id": "A", "explanation": "The key findings support the correct interpretation.",
                "educational_objective": "Apply document evidence to a clinical scenario.", "clinical_task": "diagnosis",
                "reasoning_order": "second_order", "answer_choice_category": "diagnoses", "common_trap": "Anchoring",
                "key_discriminator": "The decisive supplied finding", "teacher_note": "Identify the discriminator before comparing homogeneous answer choices.",
                "evidence_ids": ["E1"],
            })
        return "Deterministic mock answer."


def provider_from_env(name: str | None = None) -> LLMProvider:
    provider = (name or os.getenv("MEDRAG_PROVIDER", "ollama")).strip().lower()
    if provider == "ollama":
        return OllamaProvider(os.getenv("OLLAMA_URL", "http://127.0.0.1:11434"), os.getenv("OLLAMA_MODEL", "qwen3:14b"))
    if provider == "openai":
        key = os.getenv("OPENAI_API_KEY", "")
        if not key:
            raise ProviderError("OPENAI_API_KEY is required")
        return OpenAIResponsesProvider(key, os.getenv("OPENAI_MODEL", "gpt-5-mini"))
    if provider == "openai_compatible":
        key, model = os.getenv("LLM_API_KEY", ""), os.getenv("LLM_MODEL", "")
        if not key or not model:
            raise ProviderError("LLM_API_KEY and LLM_MODEL are required")
        return OpenAICompatibleProvider(os.getenv("LLM_BASE_URL", "https://openrouter.ai/api/v1"), key, model)
    if provider == "gemini":
        key = os.getenv("GEMINI_API_KEY", "")
        if not key:
            raise ProviderError("GEMINI_API_KEY is required")
        return GeminiProvider(key, os.getenv("GEMINI_MODEL", "gemini-2.5-flash"))
    if provider == "mock":
        return MockProvider()
    raise ProviderError(f"unknown provider: {provider}")


def provider_from_config(
    name: str | None = None,
    api_key: str | None = None,
    model: str | None = None,
    base_url: str | None = None,
) -> LLMProvider:
    """Create a request-scoped provider without persisting credentials."""
    provider = (name or os.getenv("MEDRAG_PROVIDER", "ollama")).strip().lower()
    api_key = (api_key or "").strip()
    model = (model or "").strip()
    base_url = (base_url or "").strip()

    if provider == "groq":
        key = api_key
        if not key:
            raise ProviderError("A Groq API key is required")
        return OpenAICompatibleProvider(base_url or "https://api.groq.com/openai/v1", key, model or "openai/gpt-oss-120b", name="groq")
    if provider == "openrouter":
        key = api_key
        selected_model = model
        if not key or not selected_model:
            raise ProviderError("An OpenRouter API key and specific model are required")
        return OpenAICompatibleProvider(base_url or "https://openrouter.ai/api/v1", key, selected_model, name="openrouter")
    if provider == "openai_compatible":
        key = api_key
        selected_model = model
        if not key or not selected_model:
            raise ProviderError("An API key and model are required")
        return OpenAICompatibleProvider(base_url or os.getenv("LLM_BASE_URL", "https://openrouter.ai/api/v1"), key, selected_model)
    if provider == "gemini":
        key = api_key
        if not key:
            raise ProviderError("A Gemini API key is required")
        return GeminiProvider(key, model or os.getenv("GEMINI_MODEL", "gemini-2.5-flash"))
    if provider == "openai":
        key = api_key
        if not key:
            raise ProviderError("An OpenAI API key is required")
        return OpenAIResponsesProvider(key, model or os.getenv("OPENAI_MODEL", "gpt-5-mini"), base_url or "https://api.openai.com/v1")
    if provider == "ollama":
        return OllamaProvider(base_url or os.getenv("OLLAMA_URL", "http://127.0.0.1:11434"), model or os.getenv("OLLAMA_MODEL", "qwen3:14b"))
    if provider == "mock":
        return MockProvider()
    raise ProviderError(f"unknown provider: {provider}")
