"""Structured trace spans for DAG nodes.

Provides a lightweight span context manager that emits structured JSON log
records for each DAG node execution. Falls back to no-ops when OpenTelemetry
is not installed, so the orchestrator never has a hard dependency on it.
"""
from __future__ import annotations

import logging
import time
from contextlib import contextmanager
from typing import Any, Dict, Generator, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Optional OpenTelemetry integration
# ---------------------------------------------------------------------------

try:
    from opentelemetry import trace as _otel_trace
    from opentelemetry.trace import Span as _OtelSpan

    _TRACER = _otel_trace.get_tracer("context-kernel")
    _OTEL_AVAILABLE = True
except ImportError:  # pragma: no cover
    _TRACER = None
    _OTEL_AVAILABLE = False


# ---------------------------------------------------------------------------
# SpanRecord — structured data collected during a span
# ---------------------------------------------------------------------------

class SpanRecord:
    """Lightweight in-process span record emitted as a structured log."""

    def __init__(self, name: str, attributes: Optional[Dict[str, Any]] = None) -> None:
        self.name = name
        self.attributes: Dict[str, Any] = attributes or {}
        self._start: float = time.monotonic()
        self.duration_ms: float = 0.0
        self.error: Optional[str] = None

    def finish(self, error: Optional[str] = None) -> None:
        self.duration_ms = round((time.monotonic() - self._start) * 1000, 2)
        self.error = error
        level = logging.ERROR if error else logging.DEBUG
        logger.log(
            level,
            "span",
            extra={
                "span_name": self.name,
                "duration_ms": self.duration_ms,
                "error": self.error,
                **self.attributes,
            },
        )


# ---------------------------------------------------------------------------
# Public context managers
# ---------------------------------------------------------------------------

@contextmanager
def trace_node(
    node_name: str,
    session_id: Optional[str] = None,
    **extra: Any,
) -> Generator[SpanRecord, None, None]:
    """Context manager that wraps a DAG node execution with a trace span.

    Usage::

        with trace_node("call_model", session_id=state.session_id) as span:
            response = complete(...)
            span.attributes["model"] = state.model_id

    When OpenTelemetry is available an OTEL span is also created so traces
    appear in any configured backend (Jaeger, Zipkin, etc.).
    """
    attrs: Dict[str, Any] = {"session_id": session_id or "", **extra}
    record = SpanRecord(node_name, attributes=attrs)

    otel_span: Optional[Any] = None
    if _OTEL_AVAILABLE and _TRACER is not None:
        ctx = _TRACER.start_as_current_span(node_name, attributes=attrs)  # type: ignore[attr-defined]
        otel_span = ctx.__enter__()

    try:
        yield record
        record.finish()
    except Exception as exc:
        record.finish(error=str(exc))
        if otel_span is not None:
            try:
                otel_span.record_exception(exc)  # type: ignore[attr-defined]
                otel_span.set_status(  # type: ignore[attr-defined]
                    _otel_trace.StatusCode.ERROR, str(exc)  # type: ignore[attr-defined]
                )
            except Exception:  # pragma: no cover
                pass
        raise
    finally:
        if otel_span is not None:
            try:
                ctx.__exit__(None, None, None)  # type: ignore[attr-defined]
            except Exception:  # pragma: no cover
                pass
