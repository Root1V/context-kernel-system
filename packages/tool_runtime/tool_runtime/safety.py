"""Safety validation layer — validates tool arguments against JSON schema."""
from __future__ import annotations

from typing import Any


class ToolArgumentValidationError(Exception):
    def __init__(self, tool_name: str, errors: list[str]) -> None:
        super().__init__(
            f"Argument validation failed for tool {tool_name!r}: {'; '.join(errors)}"
        )
        self.tool_name = tool_name
        self.errors = errors


def validate_arguments(
    tool_name: str,
    arguments: dict[str, Any],
    schema: dict[str, Any],
) -> None:
    """Validate *arguments* against the tool's JSON schema.

    Raises :class:`ToolArgumentValidationError` if validation fails.
    Uses jsonschema when available; falls back to required-fields check.
    """
    try:
        import jsonschema
        try:
            jsonschema.validate(instance=arguments, schema=schema)
        except jsonschema.ValidationError as e:
            raise ToolArgumentValidationError(tool_name, [e.message]) from e
    except ImportError:
        # Fallback: only check required fields
        _validate_required(tool_name, arguments, schema)


def _validate_required(
    tool_name: str,
    arguments: dict[str, Any],
    schema: dict[str, Any],
) -> None:
    required = schema.get("required", [])
    missing = [f for f in required if f not in arguments]
    if missing:
        raise ToolArgumentValidationError(
            tool_name, [f"Missing required field: {f!r}" for f in missing]
        )
