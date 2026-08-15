"""Safe, structured logging configuration.

Deliberately avoids logging secrets or full document bodies. Provides a
`redact` helper for scrubbing known-sensitive keys from dicts.
"""
from __future__ import annotations

import logging
import sys

_SENSITIVE_KEYS = {
    "api_key", "apikey", "password", "secret", "token", "authorization",
    "llm_api_key", "google_api_key", "access_token", "refresh_token",
}


def redact(value: object, max_len: int = 500) -> object:
    """Recursively redact sensitive keys and truncate long values."""
    if isinstance(value, dict):
        return {
            k: ("[REDACTED]" if k.lower() in _SENSITIVE_KEYS else redact(v, max_len))
            for k, v in value.items()
        }
    if isinstance(value, (list, tuple)):
        return [redact(v, max_len) for v in value]
    if isinstance(value, str) and len(value) > max_len:
        return value[:max_len] + f"...<{len(value) - max_len} more chars>"
    return value


def setup_logging(level: int = logging.INFO) -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s")
    )
    root = logging.getLogger()
    root.setLevel(level)
    root.handlers = [handler]


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
