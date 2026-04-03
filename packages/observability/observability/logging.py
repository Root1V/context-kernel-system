"""Structured JSON logging for all package public entry points.

Call `configure_logging()` once at startup to emit machine-readable JSON logs.
Packages call `get_logger(__name__)` — which returns a standard `logging.Logger`.
"""

from __future__ import annotations

import json
import logging
import sys
from typing import Any


class _StructuredFormatter(logging.Formatter):
    """Emits log records as single-line JSON objects."""

    def format(self, record: logging.LogRecord) -> str:
        base: dict[str, Any] = {
            "ts": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        # Copy any extra fields injected by trace_node or callers
        for key, value in record.__dict__.items():
            if key not in (
                "msg",
                "args",
                "levelname",
                "levelno",
                "pathname",
                "filename",
                "module",
                "exc_info",
                "exc_text",
                "stack_info",
                "lineno",
                "funcName",
                "created",
                "msecs",
                "relativeCreated",
                "thread",
                "threadName",
                "processName",
                "process",
                "name",
                "message",
                "taskName",
                "asctime",
            ):
                base[key] = value

        if record.exc_info:
            base["exc"] = self.formatException(record.exc_info)

        return json.dumps(base, default=str)


def configure_logging(level: int = logging.INFO) -> None:
    """Configure root logger to emit structured JSON to stdout.

    Should be called once at process startup (e.g., in api/main.py or
    worker/main.py). Safe to call multiple times — handlers are deduplicated.
    """
    root = logging.getLogger()
    root.setLevel(level)

    # Avoid adding duplicate handlers on repeated calls
    for h in root.handlers:
        if isinstance(h, logging.StreamHandler) and isinstance(h.formatter, _StructuredFormatter):
            return

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(_StructuredFormatter())
    root.addHandler(handler)


def get_logger(name: str) -> logging.Logger:
    """Return a logger for the given module name.

    This is a thin wrapper around ``logging.getLogger`` so packages don't
    need to import the stdlib directly — makes later swapping easier.
    """
    return logging.getLogger(name)
