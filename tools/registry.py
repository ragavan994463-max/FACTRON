"""Provider-independent FACTRON tool registry."""

from __future__ import annotations

from typing import Any, Iterable, Mapping

from .builtin import ToolDefinition, ToolResult
from .permissions import Permission, PermissionSet


class ToolRegistry:
    """Deterministic registry and execution boundary for tools."""

    def __init__(
        self,
        tools: Iterable[ToolDefinition] | None = None,
    ) -> None:
        self._tools: dict[str, ToolDefinition] = {}

        if tools is not None:
            for tool in tools:
                self.register(tool)

    @property
    def size(self) -> int:
        """Return the number of registered tools."""
        return len(self._tools)

    def register(self, tool: ToolDefinition) -> None:
        """Register one tool."""
        if not isinstance(tool, ToolDefinition):
            raise TypeError("tool must be a ToolDefinition")

        if tool.name in self._tools:
            raise ValueError(
                f"tool already registered: {tool.name}"
            )

        self._tools[tool.name] = tool

    def unregister(self, name: str) -> None:
        """Remove a registered tool."""
        normalized = self._normalize_name(name)

        if normalized not in self._tools:
            raise KeyError(f"unknown tool: {normalized}")

        del self._tools[normalized]

    def get(self, name: str) -> ToolDefinition | None:
        """Return a tool or None when it is not registered."""
        normalized = self._normalize_name(name)
        return self._tools.get(normalized)

    def names(self) -> tuple[str, ...]:
        """Return registered names in deterministic order."""
        return tuple(sorted(self._tools))

    def execute(
        self,
        name: str,
        arguments: Mapping[str, Any] | None = None,
        permissions: PermissionSet | None = None,
    ) -> ToolResult:
        """Execute a registered tool through the permission boundary."""
        normalized = self._normalize_name(name)

        tool = self._tools.get(normalized)

        if tool is None:
            return ToolResult(
                tool_name=normalized,
                success=False,
                error=f"Unknown tool: {normalized}",
            )

        supplied_permissions = (
            permissions
            if permissions is not None
            else PermissionSet()
        )

        if not isinstance(supplied_permissions, PermissionSet):
            raise TypeError(
                "permissions must be a PermissionSet"
            )

        try:
            supplied_permissions.require(tool.permission)

            kwargs = dict(arguments or {})

            output = tool.handler(**kwargs)

            return ToolResult(
                tool_name=tool.name,
                success=True,
                output=output,
            )

        except Exception as exc:
            return ToolResult(
                tool_name=tool.name,
                success=False,
                error=f"{type(exc).__name__}: {exc}",
            )

    @staticmethod
    def _normalize_name(name: str) -> str:
        """Normalize and validate a tool name."""
        if not isinstance(name, str):
            raise TypeError("tool name must be a string")

        normalized = name.strip().lower()

        if not normalized:
            raise ValueError("tool name cannot be empty")

        return normalized
