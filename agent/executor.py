"""FACTRON Omega deterministic execution subsystem."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from time import perf_counter
from typing import Any, Callable, MutableMapping


class StepStatus(str, Enum):
    """Execution status for an individual step."""

    SUCCESS = "success"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class StepAction:
    """Registered executable action."""

    name: str
    handler: Callable[..., Any]

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("action name cannot be empty")

        if not callable(self.handler):
            raise TypeError("handler must be callable")


@dataclass(slots=True)
class ExecutionContext:
    """Mutable execution state for one Agent run."""

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
    """Result of executing one step."""

    status: StepStatus
    output: Any = None
    error: str | None = None
    duration_seconds: float = 0.0

    def __post_init__(self) -> None:
        if self.status is StepStatus.SUCCESS and self.error is not None:
            raise ValueError(
                "successful execution cannot contain an error"
            )

        if self.status is StepStatus.FAILED and not self.error:
            raise ValueError(
                "failed execution requires an error"
            )

        if self.duration_seconds < 0:
            raise ValueError(
                "duration_seconds cannot be negative"
            )


class StepExecutor:
    """Registry-backed deterministic step executor."""

    def __init__(
        self,
        actions: MutableMapping[str, StepAction] | None = None,
    ) -> None:
        self._actions: dict[str, StepAction] = {}

        if actions is not None:
            for name, action in actions.items():
                self.register(name, action)

    @property
    def actions(self) -> tuple[str, ...]:
        """Return registered action names."""
        return tuple(sorted(self._actions))

    def register(
        self,
        name: str,
        action: StepAction | Callable[..., Any],
    ) -> None:
        """Register or replace an executable action."""
        normalized_name = name.strip()

        if not normalized_name:
            raise ValueError("action name cannot be empty")

        if isinstance(action, StepAction):
            if action.name != normalized_name:
                raise ValueError(
                    "StepAction name must match registry name"
                )
            normalized_action = action
        elif callable(action):
            normalized_action = StepAction(
                name=normalized_name,
                handler=action,
            )
        else:
            raise TypeError(
                "action must be StepAction or callable"
            )

        self._actions[normalized_name] = normalized_action

    def execute(
        self,
        action: str,
        arguments: dict[str, Any] | None,
        context: ExecutionContext,
    ) -> ExecutionResult:
        """Execute one registered action."""
        if not isinstance(context, ExecutionContext):
            raise TypeError(
                "context must be an ExecutionContext"
            )

        action_name = action.strip()

        if not action_name:
            raise ValueError("action cannot be empty")

        start = perf_counter()

        registered = self._actions.get(action_name)

        if registered is None:
            duration = perf_counter() - start

            return ExecutionResult(
                status=StepStatus.FAILED,
                error=f"Unknown action: {action_name}",
                duration_seconds=duration,
            )

        try:
            kwargs = dict(arguments or {})

            output = registered.handler(
                context=context,
                **kwargs,
            )

            duration = perf_counter() - start

            return ExecutionResult(
                status=StepStatus.SUCCESS,
                output=output,
                duration_seconds=duration,
            )

        except Exception as exc:
            duration = perf_counter() - start

            return ExecutionResult(
                status=StepStatus.FAILED,
                error=f"{type(exc).__name__}: {exc}",
                duration_seconds=duration,
            )
