"""Execution contracts and action registry for FACTRON Omega."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from time import perf_counter
from typing import Any, Callable, MutableMapping


class StepStatus(str, Enum):
    """Execution state of a plan step."""

    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass(frozen=True, slots=True)
class StepAction:
    """Immutable executable action contract."""

    name: str
    handler: Callable[..., Any]

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("action name cannot be empty")

        if not callable(self.handler):
            raise TypeError(
                "handler must be callable"
            )


@dataclass(slots=True)
class ExecutionContext:
    """Mutable state available during execution."""

    run_id: str
    task: str
    state: MutableMapping[str, Any] = field(
        default_factory=dict
    )
    metadata: MutableMapping[str, Any] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        if not self.run_id.strip():
            raise ValueError("run_id cannot be empty")

        if not self.task.strip():
            raise ValueError("task cannot be empty")


@dataclass(frozen=True, slots=True)
class ExecutionResult:
    """Immutable result of one executed step."""

    status: StepStatus
    output: Any = None
    error: str | None = None
    duration_seconds: float = 0.0

    def __post_init__(self) -> None:
        if not isinstance(self.status, StepStatus):
            raise TypeError(
                "status must be a StepStatus"
            )

        if self.duration_seconds < 0:
            raise ValueError(
                "duration_seconds cannot be negative"
            )

        if self.status is StepStatus.SUCCESS:
            if self.error is not None:
                raise ValueError(
                    "successful execution cannot contain an error"
                )


class StepExecutor:
    """Provider-independent action executor."""

    def __init__(
        self,
        actions: MutableMapping[str, StepAction] | None = None,
    ) -> None:
        self._actions: dict[str, StepAction] = dict(
            actions or {}
        )

    @property
    def actions(self) -> dict[str, StepAction]:
        """Return a copy of the registered action map."""
        return dict(self._actions)

    def register(
        self,
        action: StepAction,
    ) -> None:
        """Register or replace an executable action."""
        if not isinstance(action, StepAction):
            raise TypeError(
                "action must be a StepAction"
            )

        self._actions[action.name] = action

    def unregister(
        self,
        name: str,
    ) -> None:
        """Remove an action if it exists."""
        if not name.strip():
            raise ValueError(
                "action name cannot be empty"
            )

        self._actions.pop(name, None)

    def execute(
        self,
        action_name: str,
        arguments: dict[str, Any],
        context: ExecutionContext,
    ) -> ExecutionResult:
        """Execute one registered action safely."""
        if not action_name.strip():
            raise ValueError(
                "action_name cannot be empty"
            )

        if not isinstance(arguments, dict):
            raise TypeError(
                "arguments must be a dictionary"
            )

        if not isinstance(context, ExecutionContext):
            raise TypeError(
                "context must be an ExecutionContext"
            )

        action = self._actions.get(action_name)

        if action is None:
            return ExecutionResult(
                status=StepStatus.FAILED,
                error=f"Unknown action: {action_name}",
            )

        started = perf_counter()

        try:
            output = action.handler(
                context=context,
                **arguments,
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
