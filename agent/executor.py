"""Execution primitives for FACTRON agents.

This module deliberately contains no model-provider code.  It defines a
small, strongly typed execution boundary that later tool providers can
implement without coupling the agent to a particular LLM or framework.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from time import monotonic
from typing import Any, Callable, Mapping, MutableMapping, Protocol


class StepStatus(StrEnum):
    """Lifecycle states for an executable plan step."""

    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    SKIPPED = "skipped"


class StepAction(Protocol):
    """Callable contract for an executable agent action."""

    def __call__(
        self,
        context: "ExecutionContext",
        arguments: Mapping[str, Any],
    ) -> Any:
        """Execute an action using the supplied context and arguments."""


@dataclass(slots=True)
class ExecutionContext:
    """Runtime state shared across one agent execution."""

    run_id: str
    task: str
    state: MutableMapping[str, Any] = field(default_factory=dict)
    metadata: MutableMapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ExecutionResult:
    """Immutable result returned by a step execution."""

    status: StepStatus
    output: Any = None
    error: str | None = None
    duration_seconds: float = 0.0


@dataclass(slots=True)
class StepExecutor:
    """Safely execute registered actions.

    The executor is intentionally small.  Permissions, sandboxing and
    external tool policy will be supplied by FACTRON's dedicated tools and
    safety layers rather than hidden inside the agent.
    """

    actions: MutableMapping[str, StepAction] = field(default_factory=dict)

    def register(self, name: str, action: StepAction) -> None:
        """Register or replace an action under a stable name."""
        normalized = name.strip()
        if not normalized:
            raise ValueError("Action name cannot be empty.")
        self.actions[normalized] = action

    def execute(
        self,
        action_name: str,
        context: ExecutionContext,
        arguments: Mapping[str, Any] | None = None,
    ) -> ExecutionResult:
        """Execute one registered action and convert failures to results."""
        started = monotonic()
        action = self.actions.get(action_name)

        if action is None:
            return ExecutionResult(
                status=StepStatus.FAILED,
                error=f"Unknown action: {action_name}",
                duration_seconds=monotonic() - started,
            )

        try:
            output = action(context, arguments or {})
        except Exception as exc:  # boundary: convert action failures to data
            return ExecutionResult(
                status=StepStatus.FAILED,
                error=f"{type(exc).__name__}: {exc}",
                duration_seconds=monotonic() - started,
            )

        return ExecutionResult(
            status=StepStatus.SUCCEEDED,
            output=output,
            duration_seconds=monotonic() - started,
        )
