"""FACTRON Omega tool permission contracts.

Permissions are deliberately independent from concrete tool
implementations so execution policy can evolve without coupling
the registry to individual tools.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Permission(str, Enum):
    """Logical permission levels for tool execution."""

    NONE = "none"
    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"


_PERMISSION_RANK = {
    Permission.NONE: 0,
    Permission.READ: 1,
    Permission.WRITE: 2,
    Permission.EXECUTE: 3,
}


@dataclass(frozen=True, slots=True)
class PermissionSet:
    """Immutable permission policy for a tool."""

    permissions: frozenset[Permission] = frozenset()

    def allows(self, required: Permission) -> bool:
        """Return whether the policy satisfies a required permission."""
        if not isinstance(required, Permission):
            raise TypeError("required must be a Permission")

        if required is Permission.NONE:
            return True

        return required in self.permissions

    def require(self, required: Permission) -> None:
        """Raise PermissionError when permission is unavailable."""
        if not self.allows(required):
            raise PermissionError(
                f"Missing required permission: {required.value}"
            )
