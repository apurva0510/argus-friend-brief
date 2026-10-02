from __future__ import annotations

import json

import httpx
import sentry_sdk

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
        with sentry_sdk.start_span(op="gen_ai.chat", name=f"chat {self.model}") as span:
            span.set_data("gen_ai.operation.type", "ai_client")
            span.set_data("gen_ai.request.model", self.model)
            span.set_data("gen_ai.system", "ollama")
            # Prompts, responses, evidence, URLs, and exception text are not attached.
            try:
                response = httpx.post(
                    f"{self.base_url}/api/chat",
                    json=payload,
                    timeout=self.timeout_seconds,
                )
                response.raise_for_status()
                result = response.json()
                span.set_data("gen_ai.response.model", result.get("model", self.model))
                if isinstance(result.get("prompt_eval_count"), int):
                    span.set_data("gen_ai.usage.input_tokens", result["prompt_eval_count"])
                if isinstance(result.get("eval_count"), int):
                    span.set_data("gen_ai.usage.output_tokens", result["eval_count"])
                content = result["message"]["content"]
                return Brief.model_validate(json.loads(content))
            except (httpx.HTTPError, KeyError, TypeError, ValueError) as exc:
                span.set_status("internal_error")
                span.set_data("argus.error_kind", type(exc).__name__)
                raise OllamaError(f"Ollama could not produce a valid brief: {exc}") from exc
