"""FACTRON Omega agent execution subsystem."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from time import perf_counter
from typing import Any, Callable, MutableMapping


class StepStatus(str, Enum):
    """Execution state of an individual step."""

    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


StepAction = Callable[..., Any]


@dataclass(slots=True)
class ExecutionContext:
    """Mutable execution state shared across actions."""

    run_id: str
    task: str
    state: MutableMapping[str, Any] = field(default_factory=dict)
    metadata: MutableMapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.run_id.strip():
            raise ValueError("run_id cannot be empty")

        if not self.task.strip():
            raise ValueError("task cannot be empty")


@dataclass(frozen=True, slots=True)
class ExecutionResult:
    """Immutable result of executing one step."""

    status: StepStatus
    output: Any = None
    error: str | None = None
    duration_seconds: float = 0.0

    def __post_init__(self) -> None:
        if not isinstance(self.status, StepStatus):
            raise TypeError("status must be StepStatus")

        if self.duration_seconds < 0:
            raise ValueError("duration_seconds cannot be negative")

        if self.status is StepStatus.SUCCESS and self.error is not None:
            raise ValueError("successful result cannot contain an error")

        if self.status is StepStatus.FAILED and not self.error:
            raise ValueError("failed result requires an error")


class StepExecutor:
    """Provider-independent action executor."""

    def __init__(
        self,
        actions: MutableMapping[str, StepAction] | None = None,
    ) -> None:
        self._actions: dict[str, StepAction] = {}

        if actions is not None:
            for name, action in actions.items():
                self.register(name, action)

    @property
    def actions(self) -> dict[str, StepAction]:
        """Return a shallow copy of registered actions."""
        return dict(self._actions)

    def register(
        self,
        name: str,
        action: StepAction,
    ) -> None:
        """Register an executable action."""
        normalized = name.strip()

        if not normalized:
            raise ValueError("action name cannot be empty")

        if not callable(action):
            raise TypeError("action must be callable")

        self._actions[normalized] = action

    def execute(
        self,
        action: str,
        arguments: dict[str, Any] | None = None,
        context: ExecutionContext | None = None,
    ) -> ExecutionResult:
        """Execute one registered action safely."""
        normalized = action.strip()

        if not normalized:
            raise ValueError("action cannot be empty")

        if context is None:
            raise ValueError("execution context is required")

        if not isinstance(context, ExecutionContext):
            raise TypeError("context must be ExecutionContext")

        callable_action = self._actions.get(normalized)

        if callable_action is None:
            return ExecutionResult(
                status=StepStatus.FAILED,
                error=f"Unknown action: {normalized}",
            )

        kwargs = dict(arguments or {})
        started = perf_counter()

        try:
            output = callable_action(
                context=context,
                **kwargs,
            )

            duration = perf_counter() - started

            return ExecutionResult(
                status=StepStatus.SUCCESS,
                output=output,
                duration_seconds=duration,
            )

        except Exception as exc:
            duration = perf_counter() - started

            return ExecutionResult(
                status=StepStatus.FAILED,
                error=f"{type(exc).__name__}: {exc}",
                duration_seconds=duration,
            )
