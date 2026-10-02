from __future__ import annotations

from friend_brief.observability import init_sentry


def test_sentry_is_disabled_without_dsn(monkeypatch) -> None:
    monkeypatch.delenv("SENTRY_DSN", raising=False)

    assert init_sentry() is False
