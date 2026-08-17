"""Permission contracts for FACTRON Omega tools."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class PermissionLevel(str, Enum):
    """Logical permission levels for tool execution."""

    NONE = "none"
    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"


@dataclass(frozen=True, slots=True)
class ToolPermission:
    """Immutable permission declaration for a tool."""

    level: PermissionLevel = PermissionLevel.NONE
    reason: str = ""

    def __post_init__(self) -> None:
        if not isinstance(self.level, PermissionLevel):
            raise TypeError("level must be a PermissionLevel")

        if not isinstance(self.reason, str):
            raise TypeError("reason must be a string")

    def allows(self, required: PermissionLevel) -> bool:
        """Return whether this permission satisfies a requirement."""
        if not isinstance(required, PermissionLevel):
            raise TypeError("required must be a PermissionLevel")

        hierarchy = {
            PermissionLevel.NONE: 0,
            PermissionLevel.READ: 1,
            PermissionLevel.WRITE: 2,
            PermissionLevel.EXECUTE: 3,
        }

        return hierarchy[self.level] >= hierarchy[required]
