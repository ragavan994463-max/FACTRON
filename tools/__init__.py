"""FACTRON Omega tools subsystem public API."""

from .permissions import (
    PermissionLevel,
    ToolPermission,
)
from .builtin import (
    ToolCallable,
    ToolDefinition,
    add_tool,
    builtin_tools,
    echo_tool,
)
from .registry import (
    ToolExecutionResult,
    ToolRegistry,
)

__all__ = [
    "PermissionLevel",
    "ToolPermission",
    "ToolCallable",
    "ToolDefinition",
    "add_tool",
    "builtin_tools",
    "echo_tool",
    "ToolExecutionResult",
    "ToolRegistry",
]
