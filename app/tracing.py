from __future__ import annotations

import os
from typing import Any

# Load env vars BEFORE importing Langfuse — importing too early means
# Langfuse initialises with missing credentials (see instrumentation best practices).
from dotenv import load_dotenv

load_dotenv()

try:
    from langfuse import Langfuse, get_client, observe

    LANGFUSE_SDK_AVAILABLE = True
except ImportError:  # pragma: no cover - only when requirements not installed
    LANGFUSE_SDK_AVAILABLE = False

    def observe(*args: Any, **kwargs: Any):  # type: ignore[misc]
        def decorator(func):
            return func

        return decorator

    class _DummyClient:  # type: ignore[no-redef]
        def update_current_trace(self, **kwargs: Any) -> None:
            return None

        def update_current_generation(self, **kwargs: Any) -> None:
            return None

        def update_current_span(self, **kwargs: Any) -> None:
            return None

        def flush(self) -> None:
            return None

    def get_client():  # type: ignore[misc]
        return _DummyClient()


def get_langfuse_client():
    """Return the Langfuse client (or a no-op stub when SDK is unavailable)."""
    return get_client()


def flush_langfuse() -> None:
    """Flush any buffered Langfuse events — call on shutdown or in scripts."""
    if LANGFUSE_SDK_AVAILABLE:
        get_client().flush()


def tracing_enabled() -> bool:
    """Return True only when SDK is installed AND credentials are configured."""
    return LANGFUSE_SDK_AVAILABLE and bool(
        os.getenv("LANGFUSE_PUBLIC_KEY") and os.getenv("LANGFUSE_SECRET_KEY")
    )
