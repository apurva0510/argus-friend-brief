from __future__ import annotations

import json

import httpx

from friend_brief.models import Brief


class OllamaError(RuntimeError):
    """Raised when local model inference fails."""


class OllamaClient:
    def __init__(self, base_url: str, model: str, timeout_seconds: float = 120.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout_seconds = timeout_seconds

    def is_available(self) -> bool:
        try:
            response = httpx.get(f"{self.base_url}/api/tags", timeout=2.0)
            return response.is_success
        except httpx.HTTPError:
            return False

    def generate(self, system_prompt: str, user_prompt: str) -> Brief:
        payload = {
            "model": self.model,
            "stream": False,
            "format": Brief.model_json_schema(),
            "options": {"temperature": 0, "num_ctx": 16384},
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }
        try:
            response = httpx.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
            content = response.json()["message"]["content"]
            return Brief.model_validate(json.loads(content))
        except (httpx.HTTPError, KeyError, TypeError, ValueError) as exc:
            raise OllamaError(f"Ollama could not produce a valid brief: {exc}") from exc
