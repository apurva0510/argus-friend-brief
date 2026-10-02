from __future__ import annotations

import os

import sentry_sdk


def init_sentry() -> bool:
    """Initialize opt-in, metadata-only Sentry tracing."""
    dsn = os.getenv("SENTRY_DSN", "").strip()
    if not dsn:
        return False

    sentry_sdk.init(
        dsn=dsn,
        environment=os.getenv("SENTRY_ENVIRONMENT", "local"),
        traces_sample_rate=float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "1.0")),
        send_default_pii=False,
        default_integrations=False,
    )
    return True
