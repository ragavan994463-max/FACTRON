"""FACTRON Omega agent planning subsystem.

The planner converts a task and current execution context into a
deterministic execution plan.

The planning contract is intentionally provider-independent.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping, Protocol, runtime_checkable


class PlanStepStatus(str, Enum):
    """Lifecycle state of a planned step."""

    PENDING = "pending"
    READY = "ready"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass(frozen=True, slots=True)
class PlanStep:
    """Immutable executable planning step."""

    step_id: str
    action: str
    arguments: dict[str, Any] = field(default_factory=dict)
    description: str = ""
    status: PlanStepStatus = PlanStepStatus.PENDING

    def __post_init__(self) -> None:
        if not self.step_id.strip():
            raise ValueError("step_id cannot be empty")

        if not self.action.strip():
            raise ValueError("action cannot be empty")

        object.__setattr__(self, "arguments", dict(self.arguments))

        if not isinstance(self.status, PlanStepStatus):
            raise TypeError("status must be PlanStepStatus")


@dataclass(frozen=True, slots=True)
class Plan:
    """Immutable agent execution plan."""

    goal: str
    steps: tuple[PlanStep, ...]
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.goal.strip():
            raise ValueError("goal cannot be empty")

        normalized_steps = tuple(self.steps)

        if any(not isinstance(step, PlanStep) for step in normalized_steps):
            raise TypeError("all plan steps must be PlanStep instances")

        object.__setattr__(self, "steps", normalized_steps)
        object.__setattr__(self, "metadata", dict(self.metadata))


@dataclass(frozen=True, slots=True)
class PlanningContext:
    """Immutable context supplied to a planner."""

    task: str
    run_id: str
    state: Mapping[str, Any]

    def __post_init__(self) -> None:
        if not self.task.strip():
            raise ValueError("task cannot be empty")

        if not self.run_id.strip():
            raise ValueError("run_id cannot be empty")

        object.__setattr__(self, "state", dict(self.state))


@runtime_checkable
class Planner(Protocol):
    """Runtime-checkable planning interface."""

    def plan(self, context: PlanningContext) -> Plan:
        """Create an execution plan."""
        ...


class DeterministicPlanner:
    """Small deterministic planner used as the architectural baseline.

    It does not call an LLM and does not fabricate intelligence.
    More advanced planning providers can implement the Planner contract
    later without changing the AgentLoop.
    """

    def plan(self, context: PlanningContext) -> Plan:
        if not isinstance(context, PlanningContext):
            raise TypeError("context must be PlanningContext")

        action = str(
            context.state.get(
                "action",
                "observe",
            )
        ).strip()

        if not action:
            action = "observe"

        arguments = context.state.get("arguments", {})

        if not isinstance(arguments, Mapping):
            raise TypeError("planning state 'arguments' must be a mapping")

        step = PlanStep(
            step_id="step-1",
            action=action,
            arguments=dict(arguments),
            description=f"Execute planned action: {action}",
            status=PlanStepStatus.READY,
        )

        return Plan(
            goal=context.task,
            steps=(step,),
            metadata={
                "planner": "deterministic",
                "run_id": context.run_id,
            },
        )
