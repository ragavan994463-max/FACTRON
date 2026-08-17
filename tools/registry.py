"""Tool registry and controlled execution boundary for FACTRON Omega."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from .builtin import ToolDefinition, builtin_tools
from .permissions import PermissionLevel


@dataclass(frozen=True, slots=True)
class ToolExecutionResult:
    """Immutable result of a tool execution attempt."""

    tool_name: str
    success: bool
    output: Any = None
    error: str | None = None

    def __post_init__(self) -> None:
        if not self.tool_name.strip():
            raise ValueError("tool_name cannot be empty")

        if self.success and self.error is not None:
            raise ValueError(
                "successful execution cannot contain an error"
            )

        if not self.success and self.error is None:
            raise ValueError(
                "failed execution must contain an error"
            )


class ToolRegistry:
    """Deterministic registry for controlled tool discovery and execution."""

    def __init__(
        self,
        tools: tuple[ToolDefinition, ...] | None = None,
    ) -> None:
        self._tools: dict[str, ToolDefinition] = {}

        definitions = (
            builtin_tools()
            if tools is None
            else tools
        )

        for definition in definitions:
            self.register(definition)

    @property
    def size(self) -> int:
        """Return the number of registered tools."""
        return len(self._tools)

    def register(self, definition: ToolDefinition) -> None:
        """Register one tool definition."""
        if not isinstance(definition, ToolDefinition):
            raise TypeError(
                "definition must be a ToolDefinition"
            )

        name = definition.name.strip()

        if name in self._tools:
            raise ValueError(
                f"tool already registered: {name}"
            )

        self._tools[name] = definition

    def get(self, name: str) -> ToolDefinition | None:
        """Retrieve a registered tool."""
        if not isinstance(name, str):
            raise TypeError("name must be a string")

        return self._tools.get(name.strip())

    def names(self) -> tuple[str, ...]:
        """Return deterministic tool names."""
        return tuple(sorted(self._tools))

    def execute(
        self,
        name: str,
        arguments: Mapping[str, Any] | None = None,
        granted: PermissionLevel = PermissionLevel.NONE,
    ) -> ToolExecutionResult:
        """Execute a registered tool subject to permission checks."""
        if not isinstance(name, str):
            raise TypeError("name must be a string")

        if not isinstance(granted, PermissionLevel):
            raise TypeError(
                "granted must be a PermissionLevel"
            )

        tool = self.get(name)

        if tool is None:
            return ToolExecutionResult(
                tool_name=name,
                success=False,
                error=f"unknown tool: {name}",
            )

        required = tool.permission.level

        if not tool.permission.allows(required):
            return ToolExecutionResult(
                tool_name=name,
                success=False,
                error=(
                    f"permission denied: required "
                    f"{required.value}, granted {granted.value}"
                ),
            )

        if not tool.permission.allows(granted):
            return ToolExecutionResult(
                tool_name=name,
                success=False,
                error=(
                    f"permission denied: tool requires "
                    f"{required.value}, granted {granted.value}"
                ),
            )

        payload = {} if arguments is None else arguments

        if not isinstance(payload, Mapping):
            return ToolExecutionResult(
                tool_name=name,
                success=False,
                error="arguments must be a mapping",
            )

        try:
            output = tool.handler(payload)

            return ToolExecutionResult(
                tool_name=name,
                success=True,
                output=output,
            )

        except Exception as exc:
            return ToolExecutionResult(
                tool_name=name,
                success=False,
                error=f"{type(exc).__name__}: {exc}",
            )
