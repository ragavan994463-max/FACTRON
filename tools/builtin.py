"""Built-in deterministic tools for FACTRON Omega."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Mapping

from .permissions import PermissionLevel, ToolPermission


ToolCallable = Callable[[Mapping[str, Any]], Any]


@dataclass(frozen=True, slots=True)
class ToolDefinition:
    """Immutable description of a callable FACTRON tool."""

    name: str
    description: str
    handler: ToolCallable
    permission: ToolPermission = ToolPermission(
        level=PermissionLevel.NONE
    )

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("tool name cannot be empty")

        if not self.description.strip():
            raise ValueError("tool description cannot be empty")

        if not callable(self.handler):
            raise TypeError("tool handler must be callable")

        if not isinstance(self.permission, ToolPermission):
            raise TypeError(
                "permission must be a ToolPermission"
            )


def echo_tool(arguments: Mapping[str, Any]) -> Any:
    """Return the supplied value without external side effects."""
    if not isinstance(arguments, Mapping):
        raise TypeError("arguments must be a mapping")

    return arguments.get("value")


def add_tool(arguments: Mapping[str, Any]) -> float:
    """Deterministically add two numeric values."""
    if not isinstance(arguments, Mapping):
        raise TypeError("arguments must be a mapping")

    left = arguments.get("left")
    right = arguments.get("right")

    if not isinstance(left, (int, float)) or isinstance(left, bool):
        raise TypeError("left must be numeric")

    if not isinstance(right, (int, float)) or isinstance(right, bool):
        raise TypeError("right must be numeric")

    return left + right


def builtin_tools() -> tuple[ToolDefinition, ...]:
    """Return the default deterministic FACTRON tool set."""
    return (
        ToolDefinition(
            name="echo",
            description="Return a supplied value.",
            handler=echo_tool,
            permission=ToolPermission(
                level=PermissionLevel.NONE
            ),
        ),
        ToolDefinition(
            name="add",
            description="Add two numeric values.",
            handler=add_tool,
            permission=ToolPermission(
                level=PermissionLevel.READ
            ),
        ),
    )
