import json as jsonlib

import httpx

from friend_brief.ollama_client import OllamaClient


def test_generate_requests_schema_constrained_json(monkeypatch):
    captured = {}
    response_body = {
        "headline": "Evidence-led update",
        "what_changed": [],
        "why_it_matters": [],
        "bull_case": [],
        "bear_case": [],
        "watch_next": [],
        "limitations": ["Fixture response"],
    }

    def fake_post(url, *, json, timeout):
        captured.update({"url": url, "payload": json, "timeout": timeout})
        request = httpx.Request("POST", url)
        return httpx.Response(
            200,
            request=request,
            json={"message": {"content": jsonlib.dumps(response_body)}},
        )

    monkeypatch.setattr(httpx, "post", fake_post)

    brief = OllamaClient("http://localhost:11434", "gemma3:4b").generate("system", "user")

    assert brief.headline == "Evidence-led update"
    assert captured["payload"]["format"]["type"] == "object"
    assert captured["payload"]["options"]["num_ctx"] == 16384
