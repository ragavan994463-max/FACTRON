"""FACTRON state management.

State is intentionally isolated from model and persistence implementations.
Subsystems can exchange immutable snapshots while the owning state object
controls mutation.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from threading import RLock
from typing import Any, Mapping


@dataclass(frozen=True, slots=True)
class StateSnapshot:
    """Immutable point-in-time representation of FACTRON state."""

    version: int
    values: Mapping[str, Any]


class FactronState:
    """Thread-safe mutable state owner with immutable snapshots."""

    def __init__(
        self,
        initial: Mapping[str, Any] | None = None,
    ) -> None:
        self._lock = RLock()
        self._version = 0
        self._values: dict[str, Any] = deepcopy(dict(initial or {}))

    @property
    def version(self) -> int:
        """Return the current state version."""
        with self._lock:
            return self._version

    def get(
        self,
        key: str,
        default: Any = None,
    ) -> Any:
        """Read a state value using a defensive copy."""
        with self._lock:
            return deepcopy(self._values.get(key, default))

    def set(
        self,
        key: str,
        value: Any,
    ) -> int:
        """Set a value and return the resulting version."""
        if not key.strip():
            raise ValueError("State key cannot be empty.")

        with self._lock:
            self._values[key] = deepcopy(value)
            self._version += 1
            return self._version

    def update(
        self,
        values: Mapping[str, Any],
    ) -> int:
        """Atomically update multiple values."""
        if not values:
            return self.version

        if any(not key.strip() for key in values):
            raise ValueError("State keys cannot be empty.")

        with self._lock:
            for key, value in values.items():
                self._values[key] = deepcopy(value)

            self._version += 1
            return self._version

    def delete(self, key: str) -> bool:
        """Delete a value and report whether it existed."""
        with self._lock:
            if key not in self._values:
                return False

            del self._values[key]
            self._version += 1
            return True

    def snapshot(self) -> StateSnapshot:
        """Return an immutable defensive snapshot."""
        with self._lock:
            return StateSnapshot(
                version=self._version,
                values=deepcopy(self._values),
            )

    def clear(self) -> int:
        """Clear all state and increment the version."""
        with self._lock:
            self._values.clear()
            self._version += 1
            return self._version
