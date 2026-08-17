"""Deterministic built-in tools for FACTRON Omega."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Mapping

from .permissions import Permission


ToolCallable = Callable[..., Any]


@dataclass(frozen=True, slots=True)
class ToolDefinition:
    """Immutable description of a callable FACTRON tool."""

    name: str
    description: str
    handler: ToolCallable
    permission: Permission = Permission.NONE

    def __post_init__(self) -> None:
        name = self.name.strip()
        description = self.description.strip()

        if not name:
            raise ValueError("tool name cannot be empty")

        if not callable(self.handler):
            raise TypeError("tool handler must be callable")

        if not isinstance(self.permission, Permission):
            raise TypeError("permission must be a Permission")

        object.__setattr__(self, "name", name)
        object.__setattr__(self, "description", description)


@dataclass(frozen=True, slots=True)
class ToolResult:
    """Normalized result of a tool invocation."""

    tool_name: str
    success: bool
    output: Any = None
    error: str | None = None

    def __post_init__(self) -> None:
        if not self.tool_name.strip():
            raise ValueError("tool_name cannot be empty")

        if self.success and self.error is not None:
            raise ValueError(
                "successful result cannot contain an error"
            )

        if not self.success and self.error is None:
            raise ValueError(
                "failed result must contain an error"
            )


def echo(value: Any = None) -> Any:
    """Return the supplied value unchanged."""
    return value


def add(a: int | float, b: int | float) -> int | float:
    """Add two numeric values."""
    if isinstance(a, bool) or isinstance(b, bool):
        raise TypeError("boolean values are not valid numeric operands")

    if not isinstance(a, (int, float)):
        raise TypeError("a must be int or float")

    if not isinstance(b, (int, float)):
        raise TypeError("b must be int or float")

    return a + b


def builtin_tools() -> tuple[ToolDefinition, ...]:
    """Return FACTRON's deterministic built-in tool definitions."""
    return (
        ToolDefinition(
            name="echo",
            description="Return an input value unchanged.",
            handler=echo,
            permission=Permission.NONE,
        ),
        ToolDefinition(
            name="add",
            description="Add two numeric values.",
            handler=add,
            permission=Permission.NONE,
        ),
    )
